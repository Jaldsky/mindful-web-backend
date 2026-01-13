from sqlalchemy import insert as sa_insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.models.tables import AttentionEvent, User


async def insert_user_if_not_exists(session: AsyncSession, user_id) -> None:
    """Функция вставки пользователя, если его ещё нет в базе.

    Args:
        session: AsyncSession.
        user_id: ID пользователя.
    """
    stmt = pg_insert(User).values(id=user_id).on_conflict_do_nothing(index_elements=["id"])
    await session.execute(stmt)


async def bulk_insert_attention_events(session: AsyncSession, values: list[dict]) -> None:
    """Функция bulk-вставки событий внимания одним запросом.

    Args:
        session: AsyncSession.
        values: Данные для вставки ([{"user_id": ..., "domain": ..., "event_type": ..., "timestamp": ...}]).
    """
    await session.execute(sa_insert(AttentionEvent), values)
