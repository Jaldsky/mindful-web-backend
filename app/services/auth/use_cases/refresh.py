import logging
from typing import NoReturn
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..common import create_tokens, decode_token
from ..exceptions import (
    AuthServiceException,
    TokenExpiredException,
    TokenInvalidException,
    UserNotFoundException,
)
from ..queries import fetch_user_by_id
from ..types import AccessToken, RefreshToken, TokenPayload

logger = logging.getLogger(__name__)


class RefreshTokensService:
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
            raise TokenInvalidException(key="auth.errors.token_invalid", fallback="Token is invalid")

        sub = payload.get("sub")
        try:
            return UUID(str(sub))
        except (TypeError, ValueError):
            raise TokenInvalidException(key="auth.errors.token_invalid", fallback="Token is invalid")

    async def _ensure_user_exists(self, session: AsyncSession, user_id: UUID) -> None | NoReturn:
        """Приватный метод проверки существования пользователя.

        Args:
            session: Сессия базы данных.
            user_id: ID пользователя.

        Raises:
            UserNotFoundException: Если пользователь не найден.
        """
        user = await fetch_user_by_id(session, user_id)
        if not user:
            raise UserNotFoundException(
                key="auth.errors.user_not_found",
                fallback="User not found",
            )

    async def exec(
        self,
        session: AsyncSession,
        refresh_token: RefreshToken,
    ) -> tuple[AccessToken, RefreshToken] | NoReturn:
        """Метод обновления токенов (access и refresh) по старому refresh токену.

        Процесс включает:
        1. Декодирование токена обновления
        2. Проверку, что тип токена = refresh
        3. Получение user_id из sub
        4. Поиск пользователя по user_id
        5. Выпуск новой пары токенов (access и refresh)

        Args:
            session: Сессия базы данных.
            refresh_token: Токен обновления.

        Returns:
            Кортеж (access_token, refresh_token).

        Raises:
            TokenInvalidException: Если токен невалидный/не refresh.
            TokenExpiredException: Если токен обновления истёк.
            UserNotFoundException: Если пользователь не найден.
            AuthServiceException: При непредвиденной ошибке.
        """
        try:
            payload: TokenPayload = decode_token(refresh_token)
            user_id = self._extract_user_id_from_refresh_payload(payload)
            await self._ensure_user_exists(session, user_id)

            access_token, new_refresh_token = create_tokens(user_id)
            logger.info(f"Tokens refreshed for user_id={user_id}")
            return access_token, new_refresh_token

        except (TokenInvalidException, TokenExpiredException, UserNotFoundException):
            raise
        except Exception:
            raise AuthServiceException(
                key="auth.errors.auth_service_error",
                fallback="Authentication service error",
            )
