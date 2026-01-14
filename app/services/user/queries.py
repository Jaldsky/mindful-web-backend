from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..types import UserId
from ...db.models.tables import User


async def fetch_user_by_id(session: AsyncSession, user_id: UserId) -> User | None:
    """Функция получения пользователя по user_id.

    Args:
        session: AsyncSession.
        user_id: ID пользователя.

    Returns:
        Пользователь или None, если не найден.
    """
    result = await session.execute(select(User).where(and_(User.id == user_id, User.deleted_at.is_(None))))
    return result.scalar_one_or_none()
