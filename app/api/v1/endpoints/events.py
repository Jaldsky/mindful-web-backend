from uuid import UUID
from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from ...dependencies import get_user_id_from_header, get_db_session
from ....schemas.events import (
    SendEventsMethodNotAllowedSchema,
    SendEventsRequestSchema,
    SendEventsResponseSchema,
    SendEventsUnprocessableEntitySchema,
    SendEventsInternalServerErrorSchema,
)
from ....schemas.general import ServiceUnavailableSchema, BadRequestSchema
from ....services.events.send_events.main import SendEventsService

router = APIRouter(prefix="/events", tags=["events"])


@router.post(
    "/send",
    response_model=SendEventsResponseSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "model": SendEventsResponseSchema,
            "description": "События успешно сохранены",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": BadRequestSchema,
            "description": "Сырые данные не соответствуют схеме",
        },
        status.HTTP_405_METHOD_NOT_ALLOWED: {
            "model": SendEventsMethodNotAllowedSchema,
            "description": "Поддерживается только POST метод",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": SendEventsUnprocessableEntitySchema,
            "description": "Бизнес-валидация",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": SendEventsInternalServerErrorSchema,
            "description": "Внутренняя ошибка сервера",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ServiceUnavailableSchema,
            "description": "Сервис не доступен",
        },
    },
    summary="Отправка и сохранение событий",
    description=(
        "Принимает события от расширения браузера. "
        "Расширение должно передавать заголовок X-User-ID (UUID4). "
        "Если заголовок отсутствует - создаётся временный анонимный профиль."
    ),
)
async def send_events(
    payload: SendEventsRequestSchema = Body(..., description="Данные событий"),
    user_id: UUID = Depends(get_user_id_from_header),
    db: AsyncSession = Depends(get_db_session),
):
    """Ручка для приема событий от браузерного расширения.

    Args:
        payload: Схема с данными событий.
        user_id: Идентификатор пользователя из заголовка X-User-ID.
        db: Сессия базы данных.

    Returns:
        SendEventsResponseSchema: Схема успешного ответа.

    Raises:
        EventsValidationException: При ошибках бизнес-валидации (422).
        EventsServerException: При серверных ошибках (500).
    """
    await SendEventsService(session=db).exec(payload.data, user_id)

    return SendEventsResponseSchema(
        code="CREATED",
        message="Events successfully saved",
    )
