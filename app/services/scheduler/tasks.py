import asyncio
from datetime import date
from uuid import UUID
from celery import shared_task

from ...config import DEFAULT_PAGE_SIZE
from ...db.session.provider import Provider
from ..analytics.usage.main import AnalyticsUsageService


@shared_task(name="analytics.compute_domain_usage")
def compute_domain_usage_task(
    user_id: str,
    start_date: date,
    end_date: date,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> dict:
    """Celery задача вычисления статистики использования по доменам.

    Args:
        user_id: Идентификатор пользователя.
        start_date: Начало временного диапазона (объект date).
        end_date: Конец временного диапазона (объект date).
        page: Номер страницы.
        page_size: Размер страницы.

    Returns:
        Словарь с результатами аналитики.
    """
    provider = Provider()
    with provider.sync_manager.get_session() as session:
        service = AnalyticsUsageService(session, UUID(user_id))
        result_schema = asyncio.run(service.exec(start_date, end_date, page, page_size))
        return result_schema.model_dump(mode="json")
