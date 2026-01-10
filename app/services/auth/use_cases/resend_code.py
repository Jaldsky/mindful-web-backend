import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, NoReturn

from sqlalchemy.ext.asyncio import AsyncSession

from ..common import generate_verification_code, to_utc_datetime
from ..common import get_unverified_user_by_email
from ..exceptions import (
    AuthMessages,
    AuthServiceException,
    EmailAlreadyVerifiedException,
    EmailSendFailedException,
    InvalidEmailFormatException,
    TooManyAttemptsException,
    UserNotFoundException,
)
from ..normalizers import AuthServiceNormalizers
from ..validators import AuthServiceValidators
from ..queries import fetch_active_verification_code_row, update_verification_code_last_sent_at
from ...types import Email, UserId, VerificationCode
from ....config import VERIFICATION_CODE_EXPIRE_MINUTES, VERIFICATION_CODE_RESEND_COOLDOWN_SECONDS
from ....db.models.tables import User, VerificationCode as VerificationCodeModel
from ....services.email import EmailService

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class ResendVerificationCode:
    """Данные для повторной отправки кода подтверждения."""

    email: Email

    def normalize(self) -> None:
        """Метод нормализации входных данных повторной отправки кода."""
        normalized_email = AuthServiceNormalizers.normalize_email(self.email)
        if normalized_email != self.email:
            object.__setattr__(self, "email", normalized_email)

    def validate(self) -> None | NoReturn:
        """Метод валидации входных данных повторной отправки кода.

        Raises:
            InvalidEmailFormatException: При неверном формате email.
        """
        AuthServiceValidators.validate_email(self.email)


class ResendVerificationCodeServiceBase:
    """Базовый класс для сервиса повторной отправки кода подтверждения."""

    messages: type[AuthMessages] = AuthMessages
    session: AsyncSession
    _data: ResendVerificationCode

    def __init__(self, session: AsyncSession, **kwargs: Any) -> None:
        """Магический метод инициализации базового класса.

        Args:
            session: Сессия базы данных.
            **kwargs: Аргументы для ResendVerificationCode.
        """
        self.session = session
        self._data = ResendVerificationCode(**kwargs)

    @property
    def email(self) -> Email:
        """Свойство получения email из данных запроса.

        Returns:
            Email адрес пользователя.
        """
        return self._data.email

    def normalize(self) -> None:
        """Метод нормализации входных данных."""
        self._data.normalize()

    def validate(self) -> None | NoReturn:
        """Метод валидации входных данных.

        Raises:
            InvalidEmailFormatException: При неверном формате email.
        """
        self._data.validate()


class ResendVerificationCodeService(ResendVerificationCodeServiceBase):
    """Сервис повторной отправки кода подтверждения email."""

    async def _get_active_verification_code(self, user_id: UserId) -> VerificationCodeModel | None:
        """Приватный метод получения активного кода подтверждения пользователя.

        Args:
            user_id: ID пользователя.

        Returns:
            Объект VerificationCodeModel или None, если активного кода нет.
        """
        now = datetime.now(timezone.utc)
        return await fetch_active_verification_code_row(self.session, user_id, now)

    def _ensure_resend_not_rate_limited(
        self, code_row: VerificationCodeModel, current_datetime: datetime
    ) -> None | NoReturn:
        """Проверка cooldown между отправками (rate-limit) по last_sent_at/created_at.

        Args:
            code_row: Активная запись кода подтверждения.
            current_datetime: Текущее время (UTC).

        Raises:
            TooManyAttemptsException: Если повторная отправка слишком частая.
        """
        base_ts = code_row.last_sent_at or code_row.created_at
        if base_ts is None:
            return
        base_ts_utc = to_utc_datetime(base_ts)
        now_utc = to_utc_datetime(current_datetime)
        cooldown_until = base_ts_utc + timedelta(seconds=VERIFICATION_CODE_RESEND_COOLDOWN_SECONDS)
        if now_utc < cooldown_until:
            raise TooManyAttemptsException(self.messages.TOO_MANY_ATTEMPTS)

    async def _pick_or_create_code(self, user_id: UserId, current_datetime: datetime) -> tuple[VerificationCode, int]:
        """Выбор кода для отправки: reuse активного или создание нового.

        Args:
            user_id: ID пользователя.
            current_datetime: Текущее время (UTC).

        Returns:
            (code, code_row_id) — код для отправки и ID строки в verification_codes.

        Raises:
            TooManyAttemptsException: Если повторная отправка слишком частая.
        """
        active_code = await self._get_active_verification_code(user_id)
        if active_code is not None:
            self._ensure_resend_not_rate_limited(active_code, current_datetime)
            return active_code.code, active_code.id

        new_row = await self._create_verification_code_row(user_id)
        return new_row.code, new_row.id

    async def _create_verification_code_row(self, user_id: UserId) -> VerificationCodeModel:
        """Приватный метод создания записи кода подтверждения для пользователя.

        Args:
            user_id: ID пользователя.

        Returns:
            Созданная запись VerificationCode.
        """
        code: VerificationCode = generate_verification_code()
        now = datetime.now(timezone.utc)
        expires_at: datetime = now + timedelta(minutes=VERIFICATION_CODE_EXPIRE_MINUTES)
        row = VerificationCodeModel(user_id=user_id, code=code, expires_at=expires_at, created_at=now)
        self.session.add(row)
        await self.session.flush()
        return row

    async def _create_verification_code(self, user_id: UserId) -> VerificationCode:
        """Приватный метод создания кода подтверждения для пользователя.

        Args:
            user_id: ID пользователя.

        Returns:
            Сгенерированный код подтверждения.
        """
        row = await self._create_verification_code_row(user_id)
        return row.code

    async def _touch_last_sent_at(self, verification_code_id: int, at: datetime) -> None:
        """Приватный метод обновления времени последней отправки кода.

        Args:
            verification_code_id: ID записи verification_codes.
            at: Время последней отправки (UTC).
        """
        await update_verification_code_last_sent_at(self.session, verification_code_id, at)

    async def _send_verification_email(self, email: Email, code: VerificationCode) -> None | NoReturn:
        """Приватный метод отправки кода подтверждения на email.

        Args:
            email: Email адрес получателя.
            code: Код подтверждения для отправки.

        Raises:
            EmailSendFailedException: Если не удалось отправить email.
        """
        try:
            await EmailService().send_verification_code(to_email=email, code=code)
        except Exception:
            raise EmailSendFailedException(self.messages.EMAIL_SEND_FAILED)

    async def exec(self) -> bool | NoReturn:
        """Метод повторной отправки кода подтверждения.

        Процесс включает:
        1. Нормализацию входных данных
        2. Валидацию формата email
        3. Поиск пользователя по email
        4. Проверку, что email ещё не подтверждён
        5. Поиск активного кода подтверждения (used_at IS NULL, expires_at > now)
        6. Anti-spam: проверку cooldown между отправками по (last_sent_at или created_at)
        7. Переиспользование активного кода подтверждения или создание нового
        8. Фиксацию DB-фазы (transaction commit через session.begin)
        9. Отправку кода подтверждения на email
        10. Обновление last_sent_at после успешной отправки (best-effort, в отдельной транзакции)

        Returns:
            True, если код успешно выбран/создан и отправлен на email.

        Raises:
            InvalidEmailFormatException: При неверном формате email.
            UserNotFoundException: Если пользователь не найден.
            EmailAlreadyVerifiedException: Если email уже подтверждён.
            TooManyAttemptsException: Если повторная отправка слишком частая.
            EmailSendFailedException: Если не удалось отправить email.
            AuthServiceException: При неожиданной ошибке на DB-стадии или email-стадии.
        """
        self.normalize()
        self.validate()

        code: VerificationCode | None = None
        code_row_id: int | None = None
        try:
            async with self.session.begin():
                now = datetime.now(timezone.utc)
                user = await get_unverified_user_by_email(self.session, self.email, messages=self.messages)
                code, code_row_id = await self._pick_or_create_code(user.id, now)
        except (
            InvalidEmailFormatException,
            UserNotFoundException,
            EmailAlreadyVerifiedException,
            TooManyAttemptsException,
        ):
            raise
        except Exception:
            raise AuthServiceException(self.messages.RESEND_CODE_DB_STAGE_ERROR)

        if code is None:
            raise AuthServiceException(self.messages.RESEND_CODE_DB_STAGE_ERROR)

        try:
            await self._send_verification_email(self.email, code)
        except EmailSendFailedException:
            raise
        except Exception:
            raise AuthServiceException(self.messages.RESEND_CODE_EMAIL_STAGE_ERROR)

        if code_row_id is not None:
            try:
                async with self.session.begin():
                    now = datetime.now(timezone.utc)
                    await self._touch_last_sent_at(code_row_id, now)
            except Exception:
                pass

        logger.info(f"Verification code resent to: {self.email}")
        return True
