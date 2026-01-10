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
    UserNotFoundException,
    VerificationCodeExpiredException,
    VerificationCodeInvalidException,
)
from ..common import get_unverified_user_by_email
from ..common import to_utc_datetime
from ..normalizers import AuthServiceNormalizers
from ..queries import fetch_unused_verification_code_row_by_user_and_code
from ..validators import AuthServiceValidators
from ...types import Email, VerificationCode

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

    async def _get_valid_verification_code_row(self, user_id, code: VerificationCode, current_datetime: datetime):
        """Приватный метод получения валидной записи кода подтверждения.

        Args:
            user_id: ID пользователя.
            code: Код подтверждения.
            current_datetime: Текущее время (UTC).

        Returns:
            Объект записи кода подтверждения.

        Raises:
            VerificationCodeInvalidException: Если запись кода не найдена.
            VerificationCodeExpiredException: Если код истёк.
        """
        verification = await fetch_unused_verification_code_row_by_user_and_code(self.session, user_id, code)
        if not verification:
            raise VerificationCodeInvalidException(self.messages.CODE_INVALID)
        expires_at_utc = to_utc_datetime(verification.expires_at)
        now_utc = to_utc_datetime(current_datetime)
        if expires_at_utc < now_utc:
            raise VerificationCodeExpiredException(self.messages.CODE_EXPIRED)
        return verification

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
            AuthServiceException: При непредвиденной ошибке.
        """
        self.normalize()
        self.validate()

        try:
            user = await get_unverified_user_by_email(self.session, self.email, messages=self.messages)

            now = datetime.now(timezone.utc)
            verification = await self._get_valid_verification_code_row(user.id, self.code, now)

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
        ):
            await self.session.rollback()
            raise
        except Exception:
            await self.session.rollback()
            raise AuthServiceException(self.messages.AUTH_SERVICE_ERROR)
