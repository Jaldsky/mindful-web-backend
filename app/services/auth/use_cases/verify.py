import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, NoReturn

from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions import (
    AuthMessages,
    AuthServiceException,
    EmailAlreadyVerifiedException,
    InvalidVerificationCodeFormatException,
    TooManyAttemptsException,
    UserNotFoundException,
    VerificationCodeExpiredException,
    VerificationCodeInvalidException,
)
from ..common import to_utc_datetime
from ..normalizers import AuthServiceNormalizers
from ..queries import fetch_user_with_latest_verification_code_by_email
from ....config import VERIFICATION_CODE_MAX_ATTEMPTS
from ..validators import AuthServiceValidators
from ...types import Email, VerificationCode
from ....db.models.tables import User, VerificationCode as VerificationCodeModel

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class VerifyEmail:
    """Данные для подтверждения email."""

    email: Email
    code: VerificationCode

    def normalize(self) -> None:
        """Нормализация входных данных подтверждения email."""
        normalized_email = AuthServiceNormalizers.normalize_email(self.email)
        if normalized_email != self.email:
            object.__setattr__(self, "email", normalized_email)

        normalized_code = (self.code or "").strip()
        if normalized_code != self.code:
            object.__setattr__(self, "code", normalized_code)

    def validate(self) -> None | NoReturn:
        """Функция валидации входных данных подтверждения email.

        Email валидируется pydantic-схемой (EmailStr) на уровне API-схемы.

        Raises:
            InvalidVerificationCodeFormatException: Если код не валидный.
        """
        AuthServiceValidators.validate_verification_code(self.code)


class VerifyEmailServiceBase:
    """Базовый класс для сервиса подтверждения email."""

    messages: type[AuthMessages] = AuthMessages
    session: AsyncSession
    _data: VerifyEmail

    def __init__(self, session: AsyncSession, **kwargs: Any) -> None:
        """Инициализация сервиса подтверждения email.

        Args:
            session: Сессия базы данных.
            **kwargs: Аргументы для VerifyEmail.
        """
        self.session = session
        self._data = VerifyEmail(**kwargs)

    @property
    def email(self) -> Email:
        """Свойство получения email из входных данных."""
        return self._data.email

    @property
    def code(self) -> str:
        """Свойство получения кода подтверждения из входных данных."""
        return self._data.code

    def normalize(self) -> None:
        """Функция нормализации входных данных подтверждения email."""
        self._data.normalize()

    def validate(self) -> None | NoReturn:
        """Метод валидации входных данных подтверждения email.

        Raises:
            InvalidVerificationCodeFormatException: Если код не валидный.
        """
        self._data.validate()


class VerifyEmailService(VerifyEmailServiceBase):
    """Сервис подтверждения email."""

    async def _load_user_and_code_row(self) -> tuple[User, VerificationCodeModel]:
        """Приватный метод загрузки пользователя и последней записи кода подтверждения.

        Returns:
            Кортеж с пользователем и записью кода подтверждения.

        Raises:
            UserNotFoundException: Если пользователь не найден.
            EmailAlreadyVerifiedException: Если email уже подтверждён.
            TooManyAttemptsException: Если последний код был инвалидирован из-за исчерпания попыток.
            VerificationCodeInvalidException: Если нет кода подтверждения или он уже использован.
        """
        user, verification = await fetch_user_with_latest_verification_code_by_email(self.session, self.email)
        if not user:
            raise UserNotFoundException(self.messages.USER_NOT_FOUND)
        if user.is_verified:
            raise EmailAlreadyVerifiedException(self.messages.EMAIL_ALREADY_VERIFIED)
        if not verification:
            raise VerificationCodeInvalidException(self.messages.CODE_INVALID)

        if verification.used_at is not None:
            attempts = int(getattr(verification, "attempts", 0) or 0)
            if attempts >= VERIFICATION_CODE_MAX_ATTEMPTS:
                raise TooManyAttemptsException(self.messages.TOO_MANY_ATTEMPTS)
            raise VerificationCodeInvalidException(self.messages.CODE_INVALID)

        return user, verification

    def _ensure_code_not_expired(self, verification: VerificationCodeModel, now: datetime) -> None | NoReturn:
        """Приватный метод проверки срока действия кода подтверждения.

        Args:
            verification: Запись кода подтверждения.
            now: Текущее время (UTC).

        Raises:
            VerificationCodeExpiredException: Если код истёк.
        """
        expires_at_utc = to_utc_datetime(verification.expires_at)
        now_utc = to_utc_datetime(now)
        if expires_at_utc < now_utc:
            raise VerificationCodeExpiredException(self.messages.CODE_EXPIRED)

    async def _handle_attempt_limit(self, verification: VerificationCodeModel, now: datetime) -> None | NoReturn:
        """Приватный метод проверки лимита попыток ввода кода.

        Если лимит исчерпан, инвалидирует код (used_at) и коммитит, чтобы следующий resend создал новый.

        Args:
            verification: Запись кода подтверждения.
            now: Текущее время (UTC).

        Raises:
            TooManyAttemptsException: Если превышен лимит попыток.
        """
        attempts = int(getattr(verification, "attempts", 0) or 0)
        if attempts >= VERIFICATION_CODE_MAX_ATTEMPTS:
            verification.used_at = now
            await self.session.commit()
            raise TooManyAttemptsException(self.messages.TOO_MANY_ATTEMPTS)

    async def _verify_code_match(self, verification: VerificationCodeModel, now: datetime) -> None | NoReturn:
        """Приватный метод проверки совпадения кода и обработки неверного кода.

        Args:
            verification: Запись кода подтверждения.
            now: Текущее время (UTC).

        Raises:
            TooManyAttemptsException: Если после инкремента attempts достиг лимита.
            VerificationCodeInvalidException: Если код неверный и лимит ещё не достигнут.
        """
        if verification.code == self.code:
            return

        verification.attempts = int(getattr(verification, "attempts", 0) or 0) + 1
        reached_limit = verification.attempts >= VERIFICATION_CODE_MAX_ATTEMPTS
        if reached_limit:
            verification.used_at = now
        await self.session.commit()

        if reached_limit:
            raise TooManyAttemptsException(self.messages.TOO_MANY_ATTEMPTS)
        raise VerificationCodeInvalidException(self.messages.CODE_INVALID)

    async def exec(self) -> bool | NoReturn:
        """Функция подтверждения email по ранее отправленному коду.

        Процесс включает:
        1. Нормализацию входных данных
        2. Валидацию формата кода
        3. Поиск пользователя по email
        4. Проверку, что email ещё не подтверждён
        5. Поиск записи кода подтверждения
        6. Проверку, что код не истёк
        7. Пометку кода как использованного и пользователя как подтверждённого
        8. Коммит транзакции

        Returns:
            True: Если email успешно подтверждён.

        Raises:
            InvalidVerificationCodeFormatException: Если code не валидный.
            UserNotFoundException: Если пользователь не найден.
            EmailAlreadyVerifiedException: Если email уже подтверждён.
            VerificationCodeInvalidException: Если код не найден или уже использован.
            VerificationCodeExpiredException: Если код истёк.
            TooManyAttemptsException: Если превышен лимит попыток ввода кода.
            AuthServiceException: При непредвиденной ошибке.
        """
        self.normalize()
        self.validate()

        try:
            now = datetime.now(timezone.utc)
            user, verification = await self._load_user_and_code_row()
            await self._handle_attempt_limit(verification, now)
            self._ensure_code_not_expired(verification, now)
            await self._verify_code_match(verification, now)

            verification.used_at = now
            user.is_verified = True
            await self.session.commit()

            logger.info(f"Email verified: {self.email}")
            return True

        except (
            InvalidVerificationCodeFormatException,
            UserNotFoundException,
            EmailAlreadyVerifiedException,
            VerificationCodeInvalidException,
            VerificationCodeExpiredException,
            TooManyAttemptsException,
        ):
            raise
        except Exception:
            await self.session.rollback()
            raise AuthServiceException(self.messages.AUTH_SERVICE_ERROR)
