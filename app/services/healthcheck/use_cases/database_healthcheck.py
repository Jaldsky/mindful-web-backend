import logging
from typing import NoReturn

from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions import HealthcheckServiceUnavailableException
from ..queries import check_database_connection

logger = logging.getLogger(__name__)


class DatabaseHealthcheckService:
    """Сервис проверки доступности базы данных."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализация сервиса.

        Args:
            session: Сессия базы данных для проверки подключения.
        """
        self.session = session

    async def exec(self) -> None | NoReturn:
        """Проверка доступности базы данных.

        Raises:
            HealthcheckServiceUnavailableException: Если БД недоступна.
        """
        is_available = await check_database_connection(self.session)

        if not is_available:
            raise HealthcheckServiceUnavailableException("Database is not available")
