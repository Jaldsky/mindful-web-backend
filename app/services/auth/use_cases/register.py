import logging
from typing import NoReturn

from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from ..common import generate_verification_code, hash_password
from ..queries import fetch_users_by_username_or_email
from ..exceptions import (
    AuthServiceException,
    EmailAlreadyExistsException,
    EmailSendFailedException,
    InvalidEmailFormatException,
    InvalidPasswordFormatException,
    InvalidUsernameFormatException,
    UsernameAlreadyExistsException,
)
from ..types import Password, PasswordHash
from ...types import Email, UserId, VerificationCode, Username
from ....db.models.tables import User, VerificationCode as VerificationCodeModel
from ....services.email import EmailService
from ....config import VERIFICATION_CODE_EXPIRE_MINUTES

logger = logging.getLogger(__name__)


class RegisterService:
    """Сервис регистрации пользователей."""

    async def _create_verification_code(self, session: AsyncSession, user_id: UserId) -> VerificationCode:
        """Приватный метод создания кода подтверждения для пользователя.

        Args:
            session: Сессия базы данных.
            user_id: ID пользователя.

        Returns:
            Сгенерированный код подтверждения.
        """
        code: VerificationCode = generate_verification_code()
        now = datetime.now(timezone.utc)
        expires_at: datetime = now + timedelta(minutes=VERIFICATION_CODE_EXPIRE_MINUTES)
        session.add(VerificationCodeModel(user_id=user_id, code=code, expires_at=expires_at, created_at=now))
        return code

    async def _check_uniqueness(self, session: AsyncSession, username: Username, email: Email) -> None | NoReturn:
        """Приватный метод проверки уникальности username и email.

        Args:
            session: Сессия базы данных.
            username: Имя пользователя.
            email: Email адрес.

        Raises:
            UsernameAlreadyExistsException: Если username уже существует.
            EmailAlreadyExistsException: Если email уже существует.
        """
        existing_users = await fetch_users_by_username_or_email(session, username, email)

        for user in existing_users:
            if user.username == username:
                raise UsernameAlreadyExistsException(
                    key="auth.errors.username_exists",
                    fallback="User with this username already exists",
                )
            if user.email == email:
                raise EmailAlreadyExistsException(
                    key="auth.errors.email_exists",
                    fallback="User with this email already exists",
                )

    async def _create_user(
        self,
        session: AsyncSession,
        username: Username,
        email: Email,
        password: Password,
    ) -> User:
        """Приватный метод создания пользователя.

        Процесс включает:
        1. Хеширование пароля
        2. Создание объекта User
        3. Добавление пользователя в сессию

        Args:
            session: Сессия базы данных.
            username: Имя пользователя.
            email: Email адрес.
            password: Пароль пользователя.

        Returns:
            Созданный объект User.
        """
        password_hash: PasswordHash = hash_password(password)
        now = datetime.now(timezone.utc)
        user: User = User(
            username=username,
            email=email,
            password=password_hash,
            is_verified=False,
            created_at=now,
            updated_at=now,
        )
        session.add(user)
        return user

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
            raise EmailSendFailedException(
                key="auth.errors.email_send_failed",
                fallback="Failed to send verification email",
            )

    async def exec(
        self,
        session: AsyncSession,
        username: Username,
        email: Email,
        password: Password,
    ) -> User | NoReturn:
        """Метод регистрации пользователя.

        Процесс регистрации включает:
        1. Проверку уникальности username и email
        2. Создание пользователя
        3. Flush для получения ID пользователя
        4. Создание кода подтверждения
        5. Отправку кода подтверждения на email
        6. Коммит транзакции

        Args:
            session: Сессия базы данных.
            username: Имя пользователя.
            email: Email адрес.
            password: Пароль пользователя.

        Returns:
            Созданный объект User.

        Raises:
            InvalidUsernameFormatException: При неверном формате username.
            InvalidEmailFormatException: При неверном формате email.
            InvalidPasswordFormatException: При неверном формате password.
            UsernameAlreadyExistsException: Если username уже существует.
            EmailAlreadyExistsException: Если email уже существует.
            EmailSendFailedException: Если не удалось отправить email.
            AuthServiceException: При неожиданной ошибке.
        """
        try:
            await self._check_uniqueness(session, username, email)
            user = await self._create_user(session, username, email, password)
            await session.flush()
            code = await self._create_verification_code(session, user.id)
            await self._send_verification_email(email, code)

            await session.commit()
            logger.info(f"User registered: {username} ({email})")
            return user

        except (
            InvalidUsernameFormatException,
            InvalidEmailFormatException,
            InvalidPasswordFormatException,
            UsernameAlreadyExistsException,
            EmailAlreadyExistsException,
            EmailSendFailedException,
        ):
            await session.rollback()
            raise
        except Exception:
            await session.rollback()
            raise AuthServiceException(
                key="auth.errors.auth_service_error",
                fallback="Authentication service error",
            )
