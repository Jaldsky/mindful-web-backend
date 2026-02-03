import logging
from typing import NoReturn, cast

from sqlalchemy.ext.asyncio import AsyncSession

from ..common import create_tokens, verify_password
from ..exceptions import (
    AuthServiceException,
    EmailNotVerifiedException,
    InvalidCredentialsException,
)
from ..queries import fetch_user_by_username
from ..types import AccessToken, PasswordHash, RefreshToken
from ...types import Username
from ....db.models.tables import User

logger = logging.getLogger(__name__)


class LoginService:
    """Сервис авторизации пользователя."""

    async def _authenticate_user(self, session: AsyncSession, username: Username, password: str) -> User:
        """Приватный метод аутентификации пользователя.

        Процесс включает:
        1. Поиск пользователя по username
        2. Проверку наличия хэша пароля
        3. Проверку пароля
        4. Проверку подтверждения email

        Args:
            session: Сессия базы данных.
            username: Имя пользователя.
            password: Пароль пользователя.

        Returns:
            Аутентифицированный пользователь.

        Raises:
            InvalidCredentialsException: Если неверные учетные данные.
            EmailNotVerifiedException: Если email не подтверждён.
        """
        user = await fetch_user_by_username(session, username)

        if user is None or user.password is None:
            raise InvalidCredentialsException("auth.errors.invalid_credentials")

        password_hash: PasswordHash = cast(PasswordHash, user.password)

        if not verify_password(password, password_hash):
            raise InvalidCredentialsException("auth.errors.invalid_credentials")

        if not user.is_verified:
            raise EmailNotVerifiedException("auth.errors.email_not_verified")

        return user

    async def exec(
        self,
        session: AsyncSession,
        username: Username,
        password: str,
    ) -> tuple[User, AccessToken, RefreshToken] | NoReturn:
        """Метод авторизации пользователя.

        Процесс включает:
        1. Аутентификацию пользователя
        2. Выпуск access/refresh токенов

        Args:
            session: Сессия базы данных.
            username: Имя пользователя.
            password: Пароль пользователя.

        Returns:
            Кортеж (user, access_token, refresh_token).

        Raises:
            InvalidCredentialsException: Если неверные учетные данные.
            EmailNotVerifiedException: Если email не подтверждён.
            AuthServiceException: При непредвиденной ошибке.
        """
        try:
            user = await self._authenticate_user(session, username, password)
            access_token, refresh_token = create_tokens(user.id)
            logger.info(f"User logged in: {username}")
            return user, access_token, refresh_token

        except (InvalidCredentialsException, EmailNotVerifiedException):
            raise
        except Exception:
            raise AuthServiceException("auth.errors.auth_service_error")
