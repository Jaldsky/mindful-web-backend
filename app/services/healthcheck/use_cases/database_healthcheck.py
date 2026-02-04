import logging
from typing import NoReturn

from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions import HealthcheckServiceUnavailableException
from ..queries import check_database_connection

logger = logging.getLogger(__name__)


class DatabaseHealthcheckService:
    """Сервис проверки доступности базы данных."""

    async def exec(self, session: AsyncSession) -> None | NoReturn:
        """Проверка доступности базы данных.

        Args:
            session: Сессия базы данных для проверки подключения.

        Raises:
            HealthcheckServiceUnavailableException: Если БД недоступна.
        """
        is_available = await check_database_connection(session)

        if not is_available:
            raise HealthcheckServiceUnavailableException(
                key="healthcheck.errors.database_unavailable",
                fallback="Database is not available",
            )
