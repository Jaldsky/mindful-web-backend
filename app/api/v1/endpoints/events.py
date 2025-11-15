import logging
from uuid import UUID
from fastapi import APIRouter, Depends, Body, HTTPException
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from starlette import status

from ...dependencies import get_user_id_from_header, get_db_session
from ....schemas import ErrorResponseSchema, ErrorCode
from ....schemas.events.send_events_request_schema import SendEventsRequestSchema
from ....services.events.main import EventsService
from ....services.events.exceptions import EventsServiceException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["events"])


@router.post(
    "/send",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"description": "События успешно сохранены"},
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponseSchema,
            "description": "Некорректный X-User-ID или недопустимые данные",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ErrorResponseSchema,
            "description": "Ошибка валидации входных событий",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponseSchema,
            "description": "Внутренняя ошибка сервера",
        },
    },
    summary="Отправка событий в базу данных",
    description=(
        "Принимает события от расширения браузера. "
        "Расширение должно передавать заголовок X-User-ID (UUID4). "
        "Если заголовок отсутствует - создаётся временный анонимный профиль."
    ),
)
async def receive_events(
    payload: SendEventsRequestSchema = Body(..., description="Данные событий"),
    user_id: UUID = Depends(get_user_id_from_header),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Обработчик для приема событий от браузерного расширения.

    Args:
        payload: Схема с данными событий
        user_id: Идентификатор пользователя из заголовка X-User-ID
        db: Сессия базы данных

    Returns:
        Словарь с сообщением об успешном сохранении

    Raises:
        HTTPException: При ошибках валидации, базы данных или сервера
    """
    try:
        await EventsService(session=db).exec(payload, user_id)
        return
    except ValidationError as e:
        logger.error(f"Validation error for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ErrorResponseSchema(
                code=ErrorCode.VALIDATION_ERROR,
                message=f"Validation error: {str(e)}",
            ).model_dump(),
        )
    except EventsServiceException as e:
        logger.error(f"Events service error for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseSchema(
                code=ErrorCode.DATABASE_ERROR,
                message="Failed to store events",
            ).model_dump(),
        )
    except Exception as e:
        logger.error(f"Unexpected error saving events for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponseSchema(
                code=ErrorCode.INTERNAL_ERROR,
                message="Internal server error",
            ).model_dump(),
        )
