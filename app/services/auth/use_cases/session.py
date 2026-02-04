from dataclasses import dataclass
from typing import NoReturn
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..access import authenticate_access_token
from ..common import decode_token
from ..exceptions import (
    AuthServiceException,
    TokenExpiredException,
    TokenInvalidException,
    UserNotFoundException,
)
from ..types import AccessToken, SessionStatus


@dataclass(slots=True, frozen=True)
class SessionState:
    """Результат проверки текущей сессии."""

    status: SessionStatus
    user_id: UUID | None
    anon_id: UUID | None


class SessionService:
    """Сервис проверки текущей сессии."""

    async def _get_authenticated_state(
        self,
        session: AsyncSession,
        access_token: AccessToken | None,
    ) -> SessionState | None | NoReturn:
        """Приватный метод проверки токена доступа.

        Args:
            session: Сессия базы данных.
            access_token: JWT токен доступа или None.

        Returns:
            SessionState при валидном токене доступа или None.

        Raises:
            AuthServiceException: При непредвиденной ошибке сервиса.
        """
        if not access_token:
            return None
        try:
            user = await authenticate_access_token(session, access_token)
            return SessionState(status="authenticated", user_id=user.id, anon_id=None)
        except (TokenInvalidException, TokenExpiredException, UserNotFoundException):
            return None
        except Exception:
            raise AuthServiceException(
                key="auth.errors.auth_service_error",
                fallback="Authentication service error",
            )

    async def _get_anonymous_state(
        self,
        access_token: AccessToken | None,
        anon_token: AccessToken | None,
    ) -> SessionState | None | NoReturn:
        """Приватный метод проверки anon токена.

        Args:
            access_token: Не используется, для единообразия сигнатуры.
            anon_token: JWT токен анонимной сессии или None.

        Returns:
            SessionState при валидном anon токене или None.

        Raises:
            AuthServiceException: При непредвиденной ошибке сервиса.
        """
        if not anon_token:
            return None
        try:
            payload = decode_token(anon_token)
            if payload.get("type") == "anon":
                anon_id = UUID(str(payload.get("sub")))
                return SessionState(status="anonymous", user_id=None, anon_id=anon_id)
            return None
        except (TokenInvalidException, TokenExpiredException, ValueError, TypeError):
            return None
        except Exception:
            raise AuthServiceException(
                key="auth.errors.auth_service_error",
                fallback="Authentication service error",
            )

    async def exec(
        self,
        session: AsyncSession,
        access_token: AccessToken | None,
        anon_token: AccessToken | None,
    ) -> SessionState | NoReturn:
        """Метод проверки текущей сессии.

        Процесс проверки включает:
        1. Валидацию access токена (если передан)
        2. Валидацию anon токена (если access невалиден или отсутствует)
        3. Возврат статуса сессии

        Args:
            session: Сессия базы данных.
            access_token: JWT токен доступа или None.
            anon_token: JWT токен анонимной сессии или None.

        Returns:
            SessionState: Статус сессии и идентификаторы авторизированного пользователя или анонима.

        Raises:
            AuthServiceException: При непредвиденной ошибке сервиса.
        """
        authenticated_state = await self._get_authenticated_state(session, access_token)
        if authenticated_state:
            return authenticated_state

        anonymous_state = await self._get_anonymous_state(access_token, anon_token)
        if anonymous_state:
            return anonymous_state

        return SessionState(status="none", user_id=None, anon_id=None)
