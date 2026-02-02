from dataclasses import dataclass
from typing import Any, Literal, NoReturn
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..access import authenticate_access_token
from ..common import decode_token
from ..exceptions import (
    AuthMessages,
    AuthServiceException,
    TokenExpiredException,
    TokenInvalidException,
    UserNotFoundException,
)
from ..types import AccessToken, SessionStatus


@dataclass(slots=True, frozen=True)
class SessionTokens:
    """Данные текущей сессии из куки."""

    access_token: AccessToken | None
    anon_token: AccessToken | None


@dataclass(slots=True, frozen=True)
class SessionState:
    """Результат проверки текущей сессии."""

    status: SessionStatus
    user_id: UUID | None
    anon_id: UUID | None


class SessionServiceBase:
    """Базовый класс сервиса проверки текущей сессии."""

    messages: type[AuthMessages] = AuthMessages
    session: AsyncSession
    _data: SessionTokens

    def __init__(self, session: AsyncSession, **kwargs: Any) -> None:
        """Магический метод инициализации базового класса проверки сессии.

        Args:
            session: Сессия базы данных.
            **kwargs: Аргументы для SessionTokens.
        """
        self.session = session
        self._data = SessionTokens(**kwargs)

    @property
    def access_token(self) -> AccessToken | None:
        """Свойство получения access_token из входных данных.

        Returns:
            JWT токен доступа или None.
        """
        return self._data.access_token

    @property
    def anon_token(self) -> AccessToken | None:
        """Свойство получения anon_token из входных данных.

        Returns:
            JWT токен анонимной сессии или None.
        """
        return self._data.anon_token


class SessionService(SessionServiceBase):
    """Сервис проверки текущей сессии."""

    async def _get_authenticated_state(self) -> SessionState | None | NoReturn:
        """Приватный метод проверки токена доступа.

        Returns:
            SessionState при валидном токене доступа или None.

        Raises:
            AuthServiceException: При непредвиденной ошибке сервиса.
        """
        if not self.access_token:
            return None
        try:
            user = await authenticate_access_token(self.session, self.access_token)
            return SessionState(status="authenticated", user_id=user.id, anon_id=None)
        except (TokenInvalidException, TokenExpiredException, UserNotFoundException):
            return None
        except Exception:
            raise AuthServiceException("auth.errors.auth_service_error")

    async def _get_anonymous_state(self) -> SessionState | None | NoReturn:
        """Приватный метод проверки anon токена.

        Returns:
            SessionState при валидном anon токене или None.

        Raises:
            AuthServiceException: При непредвиденной ошибке сервиса.
        """
        if not self.anon_token:
            return None
        try:
            payload = decode_token(self.anon_token)
            if payload.get("type") == "anon":
                anon_id = UUID(str(payload.get("sub")))
                return SessionState(status="anonymous", user_id=None, anon_id=anon_id)
            return None
        except (TokenInvalidException, TokenExpiredException, ValueError, TypeError):
            return None
        except Exception:
            raise AuthServiceException("auth.errors.auth_service_error")

    async def exec(self) -> SessionState | NoReturn:
        """Метод проверки текущей сессии.

        Процесс проверки включает:
        1. Валидацию access токена (если передан)
        2. Валидацию anon токена (если access невалиден или отсутствует)
        3. Возврат статуса сессии

        Returns:
            SessionState: Статус сессии и идентификаторы авторизированного пользователя или анонима.

        Raises:
            AuthServiceException: При непредвиденной ошибке сервиса.
        """
        authenticated_state = await self._get_authenticated_state()
        if authenticated_state:
            return authenticated_state

        anonymous_state = await self._get_anonymous_state()
        if anonymous_state:
            return anonymous_state

        return SessionState(status="none", user_id=None, anon_id=None)
