import asyncio
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from . import common
from .types import DomainUsageRow


async def execute_domain_usage_query(
    session: Session | AsyncSession,
    *,
    user_id: str,
    start_ts: datetime,
    end_ts: datetime,
    offset: int,
    limit: int,
) -> list[DomainUsageRow]:
    """Функция выполнения SQL-запроса вычисления статистики использования доменов.

    Args:
        session: Sync или Async сессия SQLAlchemy.
        user_id: Идентификатор пользователя.
        start_ts: Начало интервала.
        end_ts: Конец интервала.
        offset: Смещение для пагинации.
        limit: Лимит для пагинации.

    Returns:
        Список строк запроса в виде словарей.
    """
    stmt = text(common.load_compute_domain_usage_sql())
    params = {
        "user_id": user_id,
        "start_ts": start_ts,
        "end_ts": end_ts,
        "offset": offset,
        "limit": limit,
    }

    if isinstance(session, AsyncSession):
        result = await session.execute(stmt, params)
    else:
        result = await asyncio.to_thread(session.execute, stmt, params)

    return list(result.mappings().all())
