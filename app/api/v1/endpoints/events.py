import logging
from uuid import UUID
from fastapi import APIRouter, Depends, Body, HTTPException
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from ...dependencies import get_user_id_from_header, get_db_session
from ....schemas import ErrorCode, ErrorDetailData
from ....schemas.events import (
    EventsErrorCode,
    SendEventsBadRequestSchema,
    SendEventsInternalServerErrorSchema,
    SendEventsMethodNotAllowedSchema,
    SendEventsRequestSchema,
    SendEventsResponseSchema,
    SendEventsUnprocessableEntitySchema,
)
from ....schemas.general import ServiceUnavailableSchema
from ....services.events.send_events.main import SendEventsService
from ....services.events.send_events.exceptions import (
    DataIntegrityViolationException,
    EventsInsertFailedException,
    EventsServiceException,
    InvalidDomainFormatException,
    InvalidDomainLengthException,
    InvalidEventTypeException,
    InvalidUserIdException,
    TimestampInFutureException,
    TransactionFailedException,
    UnexpectedEventsException,
    UserCreationFailedException,
)

logger = logging.getLogger(__name__)

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
            "model": SendEventsBadRequestSchema,
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
        HTTPException: При ошибках.
    """
    meta = payload.meta
    request_id = meta.request_id
    data = payload.data

    try:
        await SendEventsService(session=db).exec(data, user_id)
        return SendEventsResponseSchema(
            code="CREATED",
            message="Events successfully saved",
        )
    except (
        InvalidUserIdException,
        InvalidEventTypeException,
        InvalidDomainFormatException,
        InvalidDomainLengthException,
        TimestampInFutureException,
    ) as e:
        logger.error(f"[{request_id}] Business validation error: {e}", exc_info=True)

        match type(e).__name__:
            case "InvalidUserIdException":
                error_code = EventsErrorCode.INVALID_USER_ID
                error_details = [
                    ErrorDetailData(
                        field="X-User-ID",
                        message=str(e),
                        value=str(user_id),
                    )
                ]
            case "InvalidEventTypeException":
                error_code = EventsErrorCode.INVALID_EVENT_TYPE
                problematic_value = next(
                    (getattr(event, "event", None) for event in getattr(payload, "data", [])), None
                )
                error_details = [
                    ErrorDetailData(
                        field="data[].event",
                        message=str(e),
                        value=problematic_value,
                    )
                ]
            case "InvalidDomainFormatException":
                error_code = EventsErrorCode.INVALID_DOMAIN_FORMAT
                problematic_value = next(
                    (getattr(event, "domain", None) for event in getattr(payload, "data", [])), None
                )
                error_details = [
                    ErrorDetailData(
                        field="data[].domain",
                        message=str(e),
                        value=problematic_value,
                    )
                ]
            case "InvalidDomainLengthException":
                error_code = EventsErrorCode.INVALID_DOMAIN_LENGTH
                problematic_value = next(
                    (getattr(event, "domain", None) for event in getattr(payload, "data", [])), None
                )
                error_details = [
                    ErrorDetailData(
                        field="data[].domain",
                        message=str(e),
                        value=problematic_value,
                    )
                ]
            case "TimestampInFutureException":
                error_code = EventsErrorCode.TIMESTAMP_IN_FUTURE
                timestamp_value = next(
                    (getattr(event, "timestamp", None) for event in getattr(payload, "data", [])), None
                )
                problematic_value = (
                    timestamp_value.isoformat()
                    if timestamp_value and hasattr(timestamp_value, "isoformat")
                    else str(timestamp_value)
                    if timestamp_value
                    else None
                )
                error_details = [
                    ErrorDetailData(
                        field="data[].timestamp",
                        message=str(e),
                        value=problematic_value,
                    )
                ]
            case _:
                error_code = ErrorCode.VALIDATION_ERROR
                error_details = [
                    ErrorDetailData(
                        field="request",
                        message=str(e),
                        value=None,
                    )
                ]

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=SendEventsUnprocessableEntitySchema(
                code=error_code,
                message=str(e),
                details=error_details,
                meta=meta,
            ).model_dump(mode="json"),
        )
    except ValidationError as e:
        logger.error(f"[{request_id}] Payload validation error: {e}", exc_info=True)

        error_details = [
            ErrorDetailData(
                field=".".join(str(loc) for loc in err.get("loc", ())),
                message=err.get("msg", ""),
                value=err.get("input"),
            )
            for err in e.errors()
        ] or None

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=SendEventsBadRequestSchema(
                code=ErrorCode.VALIDATION_ERROR,
                message="Payload validation failed",
                details=error_details,
                meta=meta,
            ).model_dump(mode="json"),
        )
    except (
        UserCreationFailedException,
        EventsInsertFailedException,
        DataIntegrityViolationException,
        TransactionFailedException,
        UnexpectedEventsException,
        EventsServiceException,
    ) as e:
        logger.error(f"[{request_id}] Internal server error: {e}", exc_info=True)

        match type(e).__name__:
            case "UserCreationFailedException":
                error_code = EventsErrorCode.USER_CREATION_FAILED
            case "EventsInsertFailedException":
                error_code = EventsErrorCode.EVENTS_INSERT_FAILED
            case "DataIntegrityViolationException":
                error_code = EventsErrorCode.DATA_INTEGRITY_VIOLATION
            case "TransactionFailedException" | "UnexpectedEventsException":
                error_code = EventsErrorCode.TRANSACTION_FAILED
            case "EventsServiceException":
                error_code = EventsErrorCode.EVENTS_INSERT_FAILED
            case _:
                error_code = ErrorCode.INTERNAL_ERROR

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=SendEventsInternalServerErrorSchema(
                code=error_code,
                message=str(e),
                meta=meta,
            ).model_dump(mode="json"),
        )
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected internal server error: {e}", exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=SendEventsInternalServerErrorSchema(
                code=ErrorCode.INTERNAL_ERROR,
                message="Internal server error",
                meta=meta,
            ).model_dump(mode="json"),
        )
