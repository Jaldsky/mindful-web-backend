import logging
from dataclasses import dataclass
from typing import Any, NoReturn
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..common import create_tokens, decode_token
from ..exceptions import (
    AuthMessages,
    AuthServiceException,
    TokenExpiredException,
    TokenInvalidException,
    UserNotFoundException,
)
from ..queries import fetch_user_by_id
from ..types import AccessToken, RefreshToken, TokenPayload

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class RefreshTokens:
    """Данные для обновления пары токенов по refresh токену."""

    refresh_token: RefreshToken


class RefreshTokensServiceBase:
    """Базовый класс для сервиса обновления токенов."""

    messages: type[AuthMessages] = AuthMessages
    session: AsyncSession
    _data: RefreshTokens

    def __init__(self, session: AsyncSession, **kwargs: Any) -> None:
        """Магический метод инициализации базового класса обновления токенов.

        Args:
            session: Сессия базы данных.
            **kwargs: Аргументы для RefreshTokens.
        """
        self.session = session
        self._data = RefreshTokens(**kwargs)

    @property
    def refresh_token(self) -> RefreshToken:
        """Свойство получения токена обновления из входных данных.

        Returns:
            Токен обновления.
        """
        return self._data.refresh_token


class RefreshTokensService(RefreshTokensServiceBase):
    """Сервис обновления токенов (access и refresh)."""

    def _extract_user_id_from_refresh_payload(self, payload: TokenPayload) -> UUID:
        """Приватный метод извлечения user_id из payload токена обновления.

        Args:
            payload: Payload токена обновления.

        Returns:
            UUID пользователя.

        Raises:
            TokenInvalidException: Если payload не токена обновления или sub невалидный.
        """
        if payload.get("type") != "refresh":
            raise TokenInvalidException(self.messages.TOKEN_INVALID)

        sub = payload.get("sub")
        try:
            return UUID(str(sub))
        except (TypeError, ValueError):
            raise TokenInvalidException(self.messages.TOKEN_INVALID)

    async def _ensure_user_exists(self, user_id: UUID) -> None:
        """Приватный метод проверки существования пользователя.

        Args:
            user_id: ID пользователя.

        Raises:
            UserNotFoundException: Если пользователь не найден.
        """
        user = await fetch_user_by_id(self.session, user_id)
        if not user:
            raise UserNotFoundException(self.messages.USER_NOT_FOUND)

    async def exec(self) -> tuple[AccessToken, RefreshToken] | NoReturn:
        """Метод обновления токенов (access и refresh) по старому refresh токену.

        Процесс включает:
        1. Декодирование токена обновления
        2. Проверку, что тип токена = refresh
        3. Получение user_id из sub
        4. Поиск пользователя по user_id
        5. Выпуск новой пары токенов (access и refresh)

        Returns:
            Кортеж (access_token, refresh_token).

        Raises:
            TokenInvalidException: Если токен невалидный/не refresh.
            TokenExpiredException: Если токен обновления истёк.
            UserNotFoundException: Если пользователь не найден.
            AuthServiceException: При непредвиденной ошибке.
        """
        try:
            payload: TokenPayload = decode_token(self.refresh_token)
            user_id = self._extract_user_id_from_refresh_payload(payload)
            await self._ensure_user_exists(user_id)

            access_token, refresh_token = create_tokens(user_id)
            logger.info(f"Tokens refreshed for user_id={user_id}")
            return access_token, refresh_token

        except (TokenInvalidException, TokenExpiredException, UserNotFoundException):
            raise
        except Exception:
            raise AuthServiceException(self.messages.AUTH_SERVICE_ERROR)
