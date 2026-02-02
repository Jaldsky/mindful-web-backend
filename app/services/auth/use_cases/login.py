import logging
from dataclasses import dataclass
from typing import Any, NoReturn, cast

from sqlalchemy.ext.asyncio import AsyncSession

from ..common import create_tokens, verify_password
from ..exceptions import (
    AuthMessages,
    AuthServiceException,
    EmailNotVerifiedException,
    InvalidCredentialsException,
)
from ..queries import fetch_user_by_username
from ..types import AccessToken, Password, PasswordHash, RefreshToken
from ...types import Username
from ....db.models.tables import User

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class LoginUser:
    """Данные для авторизации пользователя."""

    username: Username
    password: Password


class LoginServiceBase:
    """Базовый класс сервиса авторизации пользователя."""

    messages: type[AuthMessages] = AuthMessages
    session: AsyncSession
    _data: LoginUser

    def __init__(self, session: AsyncSession, **kwargs: Any) -> None:
        """Магический метод инициализации базового класса авторизации.

        Args:
            session: Сессия базы данных.
            **kwargs: Аргументы для LoginUser.
        """
        self.session = session
        self._data = LoginUser(**kwargs)

    @property
    def username(self) -> Username:
        """Свойство получения username из входных данных."""
        return self._data.username

    @property
    def password(self) -> Password:
        """Свойство получения password из входных данных."""
        return self._data.password


class LoginService(LoginServiceBase):
    """Сервис авторизации пользователя."""

    async def _authenticate_user(self) -> User:
        """Приватный метод аутентификации пользователя.

        Процесс включает:
        1. Поиск пользователя по username
        2. Проверку наличия хэша пароля
        3. Проверку пароля
        4. Проверку подтверждения email

        Returns:
            Аутентифицированный пользователь.

        Raises:
            InvalidCredentialsException: Если неверные учетные данные.
            EmailNotVerifiedException: Если email не подтверждён.
        """
        user = await fetch_user_by_username(self.session, self.username)

        if user is None or user.password is None:
            raise InvalidCredentialsException("auth.errors.invalid_credentials")

        password_hash: PasswordHash = cast(PasswordHash, user.password)

        if not verify_password(self.password, password_hash):
            raise InvalidCredentialsException("auth.errors.invalid_credentials")

        if not user.is_verified:
            raise EmailNotVerifiedException("auth.errors.email_not_verified")

        return user

    async def exec(self) -> tuple[User, AccessToken, RefreshToken] | NoReturn:
        """Метод авторизации пользователя.

        Процесс включает:
        1. Аутентификацию пользователя
        2. Выпуск access/refresh токенов

        Returns:
            Кортеж (user, access_token, refresh_token).

        Raises:
            InvalidCredentialsException: Если неверные учетные данные.
            EmailNotVerifiedException: Если email не подтверждён.
            AuthServiceException: При непредвиденной ошибке.
        """
        try:
            user = await self._authenticate_user()
            access_token, refresh_token = create_tokens(user.id)
            logger.info("User logged in: %s", self.username)
            return user, access_token, refresh_token

        except (InvalidCredentialsException, EmailNotVerifiedException):
            raise
        except Exception:
            raise AuthServiceException("auth.errors.auth_service_error")
