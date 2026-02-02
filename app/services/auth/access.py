from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from .common import decode_token
from .exceptions import TokenInvalidException, UserNotFoundException
from .queries import fetch_user_by_id
from .types import AccessToken
from ...db.models.tables import User


def extract_user_id_from_access_token(token: AccessToken) -> UUID:
    """Функция извлечения user_id из JWT токена доступа.

    Args:
        token: JWT токен доступа.

    Returns:
        UUID пользователя из поля sub.

    Raises:
        TokenInvalidException: Если токен невалиден или не access.
        TokenExpiredException: Если токен истёк.
    """
    payload = decode_token(token)

    if payload.get("type") != "access":
        raise TokenInvalidException("auth.errors.token_invalid")

    try:
        return UUID(str(payload.get("sub")))
    except (TypeError, ValueError):
        raise TokenInvalidException("auth.errors.token_invalid")


async def authenticate_access_token(session: AsyncSession, token: AccessToken) -> User:
    """Функция аутентификации пользователя по access JWT.

    Процесс включает:
    1. Декодирование JWT и проверку срока действия токена
    2. Проверку типа токена
    3. Извлечение user_id из поля sub
    4. Поиск пользователя в базе данных по user_id

    Args:
        session: Сессия базы данных.
        token: JWT токен доступа.

    Returns:
        Текущий авторизованный пользователь.

    Raises:
        TokenInvalidException: Если токен невалиден.
        TokenExpiredException: Если токен истёк.
        UserNotFoundException: Если пользователь не найден в системе.
    """
    user_id = extract_user_id_from_access_token(token)

    user = await fetch_user_by_id(session, user_id)
    if not user:
        raise UserNotFoundException("auth.errors.user_not_found")

    return user
