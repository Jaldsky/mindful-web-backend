from fastapi import APIRouter, Body, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from ....core.localizer import localize_key
from ...dependencies import get_actor_id_from_token, get_db_session, ActorContext
from ...state_services import get_save_events_service
from ....schemas.events import (
    SaveEventsMethodNotAllowedSchema,
    SaveEventsRequestSchema,
    SaveEventsResponseSchema,
    SaveEventsUnprocessableEntitySchema,
    SaveEventsInternalServerErrorSchema,
)
from ....schemas.general import ServiceUnavailableSchema, BadRequestSchema

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
    request: Request,
    payload: SaveEventsRequestSchema = Body(..., description="Данные событий"),
    actor: ActorContext = Depends(get_actor_id_from_token),
    db: AsyncSession = Depends(get_db_session),
    save_events_service=Depends(get_save_events_service),
):
    """Принимает события от расширения браузера и сохраняет их в БД.

    Args:
        request: HTTP-запрос.
        payload: Схема с данными событий.
        actor: Контекст пользователя или анонимной сессии из JWT (access/anon).
        db: Сессия базы данных.
        save_events_service: Сервис сохранения событий (из app.state).

    Returns:
        SaveEventsResponseSchema.

    Raises:
        AnonEventsLimitExceededException: Превышен лимит событий для анонима (422).
        DataIntegrityViolationException, TransactionFailedException: Ошибки БД (500).
    """
    await save_events_service.exec(
        session=db,
        data=payload.data,
        user_id=actor.actor_id,
        actor_type=actor.actor_type,
    )

    message = localize_key(request, "events.messages.events_saved", "Events successfully saved")
    return SaveEventsResponseSchema(code="CREATED", message=message)
