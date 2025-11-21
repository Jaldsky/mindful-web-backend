import logging
from typing import Annotated
from uuid import UUID
from fastapi import Header

from ..db.session.provider import Provider
from ..db.types import DatabaseSession
from ..schemas.events import SendEventsUserIdHeaderSchema

logger = logging.getLogger(__name__)


async def get_user_id_from_header(
    x_user_id: Annotated[
        str | None,
        Header(
            alias="X-User-ID",
            description="Уникальный идентификатор пользователя (UUID4). "
            "Если не указан — создаётся временный анонимный профиль",
            example="f47ac10b-58cc-4372-a567-0e02b2c3d479",
        ),
    ] = None,
) -> UUID:
    """Функция Dependency Injection для извлечения X-User-ID из HTTP-заголовка.

    Зависимость извлекает X-User-ID из HTTP-заголовка.
    - Если заголовок отсутствует -> генерируется новый временный UUID4 (анонимный режим).
    - Если заголовок присутствует, но не является валидным UUID4 -> ошибка 400.
    - Поддерживается только UUID версии 4.

    Args:
        x_user_id: Значение HTTP-заголовка X-User-ID, переданное клиентом, None - пользователь анонимный.

    Returns:
        Валидный идентификатор пользователя UUID4.

    Raises:
        InvalidUserIdException: При неверном формате User ID (обрабатывается в events.py).
    """
    header = SendEventsUserIdHeaderSchema(**({} if x_user_id is None else {"x_user_id": x_user_id}))
    return UUID(header.x_user_id)


async def get_db_session() -> DatabaseSession:
    """Функция Dependency Injection предоставления сессии базы данных.

    Yields:
        Сессия SQLAlchemy для выполнения запросов.

    Raises:
        HTTPException: HTTP 500 Internal Server Error в случае сбоя при создании сессии.
    """
    async with Provider().async_manager.get_session() as session:
        yield session
