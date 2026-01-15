import logging
from typing import Annotated
from uuid import UUID
from fastapi import Depends, Header, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..db.session.provider import Provider
from ..db.types import DatabaseSession
from ..db.models.tables import User
from ..schemas.events import SaveEventsUserIdHeaderSchema
from ..schemas.analytics import AnalyticsUsageRequestSchema
from ..services.auth.exceptions import (
    AuthMessages,
    TokenMissingException,
)
from ..services.auth.access import authenticate_access_token, extract_user_id_from_access_token

logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=False)


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
    header = SaveEventsUserIdHeaderSchema(**({} if x_user_id is None else {"x_user_id": x_user_id}))
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


def validate_usage_request_params(
    from_date: Annotated[
        str,
        Query(alias="from", description="Начало интервала (дата в формате DD-MM-YYYY)", example="05-04-2025"),
    ],
    to_date: Annotated[
        str,
        Query(alias="to", description="Конец интервала (дата в формате DD-MM-YYYY)", example="05-04-2025"),
    ],
    page: Annotated[int, Query(ge=1, description="Номер страницы", example=1)] = 1,
) -> AnalyticsUsageRequestSchema:
    """Dependency для валидации параметров запроса analytics usage."""
    return AnalyticsUsageRequestSchema(
        from_date=from_date,
        to_date=to_date,
        page=page,
    )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: DatabaseSession = Depends(get_db_session),
) -> User:
    """Функция получения текущего пользователя по JWT токену доступа (Bearer).

    Процесс проверки включает:
    1. Проверку наличия заголовка Authorization: Bearer <token>
    2. Декодирование JWT и проверку срока действия токена
    3. Проверку типа токена
    4. Извлечение user_id из поля sub
    5. Поиск пользователя в базе данных по user_id

    Args:
        credentials: Bearer-токен из заголовка Authorization.
        db: Сессия базы данных.

    Returns:
        Текущий авторизованный пользователь.

    Raises:
        TokenMissingException: Если заголовок Authorization отсутствует.
        TokenInvalidException: Если токен невалиден/не access/содержит некорректный sub.
        TokenExpiredException: Если токен истёк.
        UserNotFoundException: Если пользователь не найден в системе.
    """
    if credentials is None:
        raise TokenMissingException(AuthMessages.TOKEN_MISSING)

    return await authenticate_access_token(db, credentials.credentials)


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> UUID:
    """Функция получения user_id текущего пользователя по JWT токену доступа.

    Args:
        credentials: Bearer-токен из заголовка Authorization.

    Returns:
        UUID пользователя.

    Raises:
        TokenMissingException: Если заголовок Authorization отсутствует.
        TokenInvalidException: Если токен невалиден.
        TokenExpiredException: Если токен истёк.
    """
    if credentials is None:
        raise TokenMissingException(AuthMessages.TOKEN_MISSING)

    return extract_user_id_from_access_token(credentials.credentials)
