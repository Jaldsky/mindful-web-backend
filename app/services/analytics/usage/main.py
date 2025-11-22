import logging
import os
import asyncio
from abc import ABC, abstractmethod
from datetime import date, datetime, time, timezone
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ....config import DEFAULT_PAGE_SIZE
from ....schemas.analytics.usage.response_ok_schema import (
    AnalyticsUsageResponseOkSchema,
    DomainUsageData,
    PaginationMeta,
)
from ....common.common import read_text_file
from .exceptions import (
    DatabaseQueryFailedException,
    UsageServiceMessages,
    UnexpectedUsageException,
)

logger = logging.getLogger(__name__)


class AnalyticsUsageServiceBase(ABC):
    """Базовый класс сервиса аналитики использования."""

    messages = UsageServiceMessages

    def __init__(self, session: Session, user_id: UUID) -> None:
        """Инициализация класса.

        Args:
            session: Сессия с базой данных.
            user_id: Идентификатор пользователя.
        """
        self.session = session
        self.user_id = user_id

    @abstractmethod
    async def exec(self, *args, **kwargs):
        """Метод выполнения основной логики."""


class AnalyticsUsageService(AnalyticsUsageServiceBase):
    """Класс сервиса аналитики использования."""

    @staticmethod
    def _normalize_pagination(page: int, page_size: int) -> tuple[int, int]:
        """Метод нормализации параметров пагинации.

        Args:
            page: Номер страницы.
            page_size: Размер страницы.

        Returns:
            Кортеж из нормализованных значений.
        """
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = DEFAULT_PAGE_SIZE
        return page, page_size

    @staticmethod
    def _build_time_range(start_date: date, end_date: date) -> tuple[datetime, datetime]:
        """Метод построения временного диапазона.

        Args:
            start_date: Начальная дата.
            end_date: Конечная дата.

        Returns:
            Кортеж из начального и конечного datetime в UTC.
        """
        start_dt = datetime.combine(start_date, time.min).replace(tzinfo=timezone.utc)
        end_dt = datetime.combine(end_date, time.max).replace(tzinfo=timezone.utc)
        return start_dt, end_dt

    @staticmethod
    def _load_sql() -> str:
        """Метод загрузки SQL запроса из файла.

        Returns:
            Строка с SQL запросом.
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        sql_path = os.path.join(base_dir, "sql", "compute_domain_usage.sql")
        return read_text_file(sql_path, encoding="utf-8")

    async def _execute_query(self, sql_text: str, params: dict):
        """Метод выполнения SQL запроса.

        Args:
            sql_text: Текст SQL запроса.
            params: Параметры для запроса.

        Returns:
            Список результатов запроса в виде словарей.
        """
        stmt = text(sql_text)
        if isinstance(self.session, AsyncSession):
            result = await self.session.execute(stmt, params)
        else:
            result = await asyncio.to_thread(self.session.execute, stmt, params)
        return result.mappings().all()

    async def exec(
        self,
        start_date: date,
        end_date: date,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> AnalyticsUsageResponseOkSchema:
        """Метод выполнения основной логики.

        Args:
            start_date: Начальная дата периода аналитики.
            end_date: Конечная дата периода аналитики.
            page: Номер страницы для пагинации.
            page_size: Размер страницы для пагинации.

        Returns:
            Схема ответа с данными аналитики использования.

        Raises:
            DatabaseQueryFailedException: При ошибке запроса к базе данных.
            UnexpectedUsageException: При неожиданной ошибке.
        """
        try:
            page, page_size = self._normalize_pagination(page, page_size)
            start_dt, end_dt = self._build_time_range(start_date, end_date)

            sql_text = self._load_sql()
            params = {
                "user_id": str(self.user_id),
                "start_ts": start_dt,
                "end_ts": end_dt,
                "offset": (page - 1) * page_size,
                "limit": page_size,
            }

            rows = await self._execute_query(sql_text, params)
            total_items = rows[0]["total_items"] if rows else 0

            pagination_meta = PaginationMeta(
                page=page,
                per_page=page_size,
                total_items=int(total_items),
                total_pages=(total_items + page_size - 1) // page_size if page_size > 0 else 0,
                next=None,
                prev=None,
            )
            data = [
                DomainUsageData(domain=r["domain"], category=r["category"], total_seconds=int(r["total_seconds"]))
                for r in rows
            ]

            logger.info(f"Successfully computed usage analytics (async, 1 SQL) for user {self.user_id}")

            return AnalyticsUsageResponseOkSchema(
                code="OK",
                message="Usage analytics computed",
                from_date=start_date,
                to_date=end_date,
                pagination=pagination_meta,
                data=data,
            )
        except SQLAlchemyError as e:
            logger.error(f"Failed to query database for async usage analytics: {e}")
            raise DatabaseQueryFailedException(self.messages.DATABASE_QUERY_ERROR)
        except Exception as e:
            logger.error(f"Unexpected error while computing async usage analytics for user {self.user_id}: {e}")
            raise UnexpectedUsageException(self.messages.UNEXPECTED_ERROR)
