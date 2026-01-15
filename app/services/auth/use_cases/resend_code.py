import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, NoReturn

from sqlalchemy.ext.asyncio import AsyncSession

from ..common import generate_verification_code, to_utc_datetime
from ..exceptions import (
    AuthMessages,
    AuthServiceException,
    EmailAlreadyVerifiedException,
    EmailSendFailedException,
    InvalidEmailFormatException,
    TooManyAttemptsException,
    UserNotFoundException,
)
from ..queries import (
    fetch_user_with_active_verification_code_by_email,
    update_verification_code_last_sent_at,
)
from ....config import VERIFICATION_CODE_MAX_ATTEMPTS
from ...types import Email, UserId, VerificationCode
from ....config import VERIFICATION_CODE_EXPIRE_MINUTES, VERIFICATION_CODE_RESEND_COOLDOWN_SECONDS
from ....db.models.tables import User, VerificationCode as VerificationCodeModel
from ....services.email import EmailService

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class ResendVerificationCode:
    """Данные для повторной отправки кода подтверждения."""

    email: Email


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


class ResendVerificationCodeService(ResendVerificationCodeServiceBase):
    """Сервис повторной отправки кода подтверждения email."""

    def _ensure_resend_not_rate_limited(
        self, code_row: VerificationCodeModel, current_datetime: datetime
    ) -> None | NoReturn:
        """Приватный метод проверки cooldown между отправками.

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

    async def _pick_or_create_code(
        self,
        user_id: UserId,
        current_datetime: datetime,
        active_code_row: VerificationCodeModel | None,
    ) -> tuple[VerificationCode, int]:
        """Приватный метод выбора кода для отправки.

        Args:
            user_id: ID пользователя.
            current_datetime: Текущее время (UTC).
            active_code_row: Активная запись кода подтверждения или None, если активного кода нет.

        Returns:
            Кортеж (code, code_row_id):
            - code: Код подтверждения для отправки.
            - code_row_id: ID строки verification_codes для последующего обновления last_sent_at.

        Raises:
            TooManyAttemptsException: Если повторная отправка слишком частая.
        """
        if active_code_row is not None:
            attempts = int(getattr(active_code_row, "attempts", 0) or 0)
            if attempts < VERIFICATION_CODE_MAX_ATTEMPTS:
                self._ensure_resend_not_rate_limited(active_code_row, current_datetime)
                return active_code_row.code, active_code_row.id

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

    async def exec(self) -> None | NoReturn:
        """Метод повторной отправки кода подтверждения.

        Процесс включает:
        1. Поиск пользователя по email
        2. Проверку, что email ещё не подтверждён
        3. Поиск активного кода подтверждения
        4. Проверку cooldown между отправками
        5. Переиспользование активного кода подтверждения или создание нового
        6. Фиксацию DB-фазы
        7. Отправку кода подтверждения на email
        8. Обновление last_sent_at после успешной отправки

        Raises:
            InvalidEmailFormatException: При неверном формате email.
            UserNotFoundException: Если пользователь не найден.
            EmailAlreadyVerifiedException: Если email уже подтверждён.
            TooManyAttemptsException: Если повторная отправка слишком частая.
            EmailSendFailedException: Если не удалось отправить email.
            AuthServiceException: При неожиданной ошибке на DB-стадии или email-стадии.
        """
        code: VerificationCode | None = None
        code_row_id: int | None = None

        try:
            async with self.session.begin():
                now = datetime.now(timezone.utc)
                user, active_code_row = await fetch_user_with_active_verification_code_by_email(
                    self.session, self.email, now
                )
                if not user:
                    raise UserNotFoundException(self.messages.USER_NOT_FOUND)
                is_pending_email = user.pending_email is not None and user.pending_email == self.email
                if user.is_verified and not is_pending_email:
                    raise EmailAlreadyVerifiedException(self.messages.EMAIL_ALREADY_VERIFIED)

                code, code_row_id = await self._pick_or_create_code(user.id, now, active_code_row)
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
