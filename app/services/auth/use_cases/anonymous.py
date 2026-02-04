import logging
from typing import NoReturn
from uuid import UUID, uuid4

from ..common import create_anon_token
from ..exceptions import AuthServiceException
from ..types import AccessToken

logger = logging.getLogger(__name__)


class AnonymousServiceBase:
    """Базовый класс сервиса создания анонимной сессии."""


class AnonymousService(AnonymousServiceBase):
    """Сервис создания анонимной сессии."""

    async def exec(self) -> tuple[UUID, AccessToken] | NoReturn:
        """Метод создания анонимной сессии.

        Процесс включает:
        1. Генерацию anon_id
        2. Создание токена анонимной сессии

        Returns:
            Кортеж (anon_id, anon_token).

        Raises:
            AuthServiceException: При ошибке генерации anon_id.
            AuthServiceException: При ошибке создания anon_token.
        """
        try:
            anon_id = uuid4()
        except Exception:
            raise AuthServiceException(
                key="auth.errors.anon_id_generation_failed",
                fallback="Failed to generate anonymous session id",
            )

        try:
            anon_token: AccessToken = create_anon_token(anon_id)
        except Exception:
            raise AuthServiceException(
                key="auth.errors.anon_token_create_failed",
                fallback="Failed to create anonymous session token",
            )

        logger.info(f"Anonymous session created: {anon_id}")
        return anon_id, anon_token
