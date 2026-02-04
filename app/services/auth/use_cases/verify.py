import logging
from datetime import datetime, timezone
from typing import NoReturn

from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions import (
    AuthServiceException,
    EmailAlreadyVerifiedException,
    InvalidVerificationCodeFormatException,
    TooManyAttemptsException,
    UserNotFoundException,
    VerificationCodeExpiredException,
    VerificationCodeInvalidException,
)
from ..common import to_utc_datetime
from ..queries import fetch_user_with_latest_verification_code_by_email
from ....config import VERIFICATION_CODE_MAX_ATTEMPTS
from ...types import Email, VerificationCode
from ....db.models.tables import User, VerificationCode as VerificationCodeModel

logger = logging.getLogger(__name__)


class VerifyEmailService:
    """Сервис подтверждения email."""

    async def _load_user_and_code_row(
        self, session: AsyncSession, email: Email
    ) -> tuple[User, VerificationCodeModel, bool]:
        """Приватный метод загрузки пользователя и последней записи кода подтверждения.

        Args:
            session: Сессия базы данных.
            email: Email адрес.

        Returns:
            Кортеж с пользователем, записью кода подтверждения и флагом pending-email.

        Raises:
            UserNotFoundException: Если пользователь не найден.
            EmailAlreadyVerifiedException: Если email уже подтверждён и pending_email отсутствует.
            TooManyAttemptsException: Если последний код был инвалидирован из-за исчерпания попыток.
            VerificationCodeInvalidException: Если нет кода подтверждения или он уже использован.
        """
        user, verification = await fetch_user_with_latest_verification_code_by_email(session, email)
        if not user:
            raise UserNotFoundException(
                key="auth.errors.user_not_found",
                fallback="User not found",
            )
        is_pending_email = user.pending_email is not None and user.pending_email == email
        if user.is_verified and not is_pending_email:
            raise EmailAlreadyVerifiedException(
                key="auth.errors.email_already_verified",
                fallback="Email is already verified",
            )
        if not verification:
            raise VerificationCodeInvalidException(
                key="auth.errors.code_invalid",
                fallback="Verification code is invalid",
            )

        if verification.used_at is not None:
            attempts = int(getattr(verification, "attempts", 0) or 0)
            if attempts >= VERIFICATION_CODE_MAX_ATTEMPTS:
                raise TooManyAttemptsException(
                    key="auth.errors.too_many_attempts",
                    fallback="Too many attempts. Please try again later",
                )
            raise VerificationCodeInvalidException(
                key="auth.errors.code_invalid",
                fallback="Verification code is invalid",
            )

        return user, verification, is_pending_email

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
            raise VerificationCodeExpiredException(
                key="auth.errors.code_expired",
                fallback="Verification code has expired",
            )

    async def _handle_attempt_limit(
        self,
        session: AsyncSession,
        verification: VerificationCodeModel,
        now: datetime,
    ) -> None | NoReturn:
        """Приватный метод проверки лимита попыток ввода кода.

        Если лимит исчерпан, инвалидирует код (used_at) и коммитит.

        Args:
            session: Сессия базы данных.
            verification: Запись кода подтверждения.
            now: Текущее время (UTC).

        Raises:
            TooManyAttemptsException: Если превышен лимит попыток.
        """
        attempts = int(getattr(verification, "attempts", 0) or 0)
        if attempts >= VERIFICATION_CODE_MAX_ATTEMPTS:
            verification.used_at = now
            await session.commit()
            raise TooManyAttemptsException(
                key="auth.errors.too_many_attempts",
                fallback="Too many attempts. Please try again later",
            )

    async def _verify_code_match(
        self,
        session: AsyncSession,
        verification: VerificationCodeModel,
        code: VerificationCode,
        now: datetime,
    ) -> None | NoReturn:
        """Приватный метод проверки совпадения кода и обработки неверного кода.

        Args:
            session: Сессия базы данных.
            verification: Запись кода подтверждения.
            code: Введённый код подтверждения.
            now: Текущее время (UTC).

        Raises:
            TooManyAttemptsException: Если после инкремента attempts достиг лимита.
            VerificationCodeInvalidException: Если код неверный и лимит ещё не достигнут.
        """
        if verification.code == code:
            return

        verification.attempts = int(getattr(verification, "attempts", 0) or 0) + 1
        reached_limit = verification.attempts >= VERIFICATION_CODE_MAX_ATTEMPTS
        if reached_limit:
            verification.used_at = now
        await session.commit()

        if reached_limit:
            raise TooManyAttemptsException(
                key="auth.errors.too_many_attempts",
                fallback="Too many attempts. Please try again later",
            )
        raise VerificationCodeInvalidException(
            key="auth.errors.code_invalid",
            fallback="Verification code is invalid",
        )

    async def exec(
        self,
        session: AsyncSession,
        email: Email,
        code: VerificationCode,
    ) -> None | NoReturn:
        """Метод подтверждения email по ранее отправленному коду.

        Процесс включает:
        1. Поиск пользователя по email или pending_email
        2. Проверку, что email ещё не подтверждён или подтверждается pending_email
        3. Поиск записи кода подтверждения
        4. Проверку, что код не истёк
        5. Пометку кода как использованного и подтверждение email
        6. Коммит транзакции

        Args:
            session: Сессия базы данных.
            email: Email адрес.
            code: Код подтверждения.

        Raises:
            InvalidVerificationCodeFormatException: Если code не валидный.
            UserNotFoundException: Если пользователь не найден.
            EmailAlreadyVerifiedException: Если email уже подтверждён.
            VerificationCodeInvalidException: Если код не найден или уже использован.
            VerificationCodeExpiredException: Если код истёк.
            TooManyAttemptsException: Если превышен лимит попыток ввода кода.
            AuthServiceException: При непредвиденной ошибке.
        """
        try:
            now = datetime.now(timezone.utc)
            user, verification, is_pending_email = await self._load_user_and_code_row(session, email)
            await self._handle_attempt_limit(session, verification, now)
            self._ensure_code_not_expired(verification, now)
            await self._verify_code_match(session, verification, code, now)

            verification.used_at = now
            if is_pending_email:
                user.email = user.pending_email
                user.pending_email = None
                user.updated_at = now
            user.is_verified = True
            await session.commit()

            logger.info(f"Email verified: {email}")

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
            await session.rollback()
            raise AuthServiceException(
                key="auth.errors.auth_service_error",
                fallback="Authentication service error",
            )
