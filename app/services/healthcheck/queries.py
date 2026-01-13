from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def check_database_connection(session: AsyncSession) -> bool:
    """Функция проверки подключения к базе данных.

    Args:
        session: AsyncSession.

    Returns:
        True если БД доступна и вернула ожидаемый результат, False в противном случае.
    """
    try:
        result = await session.execute(text("SELECT 1"))
        return result.scalar() == 1
    except Exception:
        return False
