from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from ...dependencies import get_actor_id_from_token, get_db_session, ActorContext
from ....schemas.events import (
    SaveEventsMethodNotAllowedSchema,
    SaveEventsRequestSchema,
    SaveEventsResponseSchema,
    SaveEventsUnprocessableEntitySchema,
    SaveEventsInternalServerErrorSchema,
)
from ....schemas.general import ServiceUnavailableSchema, BadRequestSchema
from ....services.events import SaveEventsService

router = APIRouter(prefix="/events", tags=["events"])


@router.post(
    "/save",
    response_model=SaveEventsResponseSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "model": SaveEventsResponseSchema,
            "description": "События успешно сохранены",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": BadRequestSchema,
            "description": "Сырые данные не соответствуют схеме",
        },
        status.HTTP_405_METHOD_NOT_ALLOWED: {
            "model": SaveEventsMethodNotAllowedSchema,
            "description": "Поддерживается только POST метод",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": SaveEventsUnprocessableEntitySchema,
            "description": "Бизнес-валидация",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": SaveEventsInternalServerErrorSchema,
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
        "Расширение должно передавать Authorization: Bearer <token>. "
        "Допускаются токены access (зарегистрированный пользователь) или anon (анонимная сессия)."
    ),
)
async def save_events(
    payload: SaveEventsRequestSchema = Body(..., description="Данные событий"),
    actor: ActorContext = Depends(get_actor_id_from_token),
    db: AsyncSession = Depends(get_db_session),
):
    """Ручка для приема событий от браузерного расширения.

    Args:
        payload: Схема с данными событий.
        actor: Контекст пользователя или анонимной сессии из JWT.
        db: Сессия базы данных.

    Returns:
        SaveEventsResponseSchema: Схема успешного ответа.

    Raises:
        EventsValidationException: При ошибках бизнес-валидации (422).
        EventsServerException: При серверных ошибках (500).
    """
    await SaveEventsService(
        session=db,
        data=payload.data,
        user_id=actor.actor_id,
        actor_type=actor.actor_type,
    ).exec()

    return SaveEventsResponseSchema(
        code="CREATED",
        message="Events successfully saved",
    )
