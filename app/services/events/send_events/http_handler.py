import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse

from ....schemas import ErrorCode, ErrorDetailData
from ....schemas.events import (
    EventsErrorCode,
    SendEventsInternalServerErrorSchema,
    SendEventsMethodNotAllowedSchema,
    SendEventsUnprocessableEntitySchema,
)
from .exceptions import EventsServerException, EventsBusinessValidationException

logger = logging.getLogger(__name__)


def send_events_method_not_allowed_response() -> JSONResponse:
    """Возвращает ответ для ошибки 405 Method Not Allowed для эндпоинта send_events.

    Returns:
        JSONResponse с ошибкой 405 Method Not Allowed.
    """
    error_schema = SendEventsMethodNotAllowedSchema(
        code=ErrorCode.METHOD_NOT_ALLOWED,
        message="Method not allowed. Only POST method is supported for this endpoint.",
    )
    return JSONResponse(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        content=error_schema.model_dump(mode="json"),
    )


def send_events_business_validation_exception_response(
    request: Request, exc: EventsBusinessValidationException
) -> JSONResponse:
    """Возвращает ответ для ошибки 422 Unprocessable Entity для эндпоинта send_events.

    Args:
        request: Объект HTTP запроса.
        exc: Исключение.

    Returns:
        JSONResponse с ошибкой 422 Unprocessable Entity.
    """
    message = str(exc)
    error_code = ErrorCode.BUSINESS_VALIDATION_ERROR
    error_details = None

    match type(exc).__name__:
        case "InvalidUserIdException":
            error_code = EventsErrorCode.INVALID_USER_ID
            user_id = request.headers.get("X-User-ID", "unknown")
            error_details = [
                ErrorDetailData(
                    field="X-User-ID",
                    message=message,
                    value=user_id,
                )
            ]
        case "InvalidEventTypeException":
            error_code = EventsErrorCode.INVALID_EVENT_TYPE
            error_details = [
                ErrorDetailData(
                    field="data[].event",
                    message=message,
                    value=None,
                )
            ]
        case "InvalidDomainFormatException":
            error_code = EventsErrorCode.INVALID_DOMAIN_FORMAT
            error_details = [
                ErrorDetailData(
                    field="data[].domain",
                    message=message,
                    value=None,
                )
            ]
        case "InvalidDomainLengthException":
            error_code = EventsErrorCode.INVALID_DOMAIN_LENGTH
            error_details = [
                ErrorDetailData(
                    field="data[].domain",
                    message=message,
                    value=None,
                )
            ]
        case "TimestampInFutureException":
            error_code = EventsErrorCode.TIMESTAMP_IN_FUTURE
            error_details = [
                ErrorDetailData(
                    field="data[].timestamp",
                    message=message,
                    value=None,
                )
            ]

    logger.warning(f"Events validation error: {message}")

    error_schema = SendEventsUnprocessableEntitySchema(
        code=error_code,
        message=message,
        details=error_details,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_schema.model_dump(mode="json"),
    )


def send_events_server_exception_response(request: Request, exc: EventsServerException) -> JSONResponse:
    """Возвращает ответ для ошибки 500 Internal Server Error.

    Args:
        request: Объект HTTP запроса.
        exc: Исключение.

    Returns:
        JSONResponse с ошибкой 500 Internal Server Error.
    """
    message = str(exc)
    error_code = ErrorCode.INTERNAL_ERROR

    match type(exc).__name__:
        case "UserCreationFailedException":
            error_code = EventsErrorCode.USER_CREATION_FAILED
        case "EventsInsertFailedException":
            error_code = EventsErrorCode.EVENTS_INSERT_FAILED
        case "DataIntegrityViolationException":
            error_code = EventsErrorCode.DATA_INTEGRITY_VIOLATION
        case "TransactionFailedException" | "UnexpectedEventsException":
            error_code = EventsErrorCode.TRANSACTION_FAILED

    logger.error(f"Events server error: {message}", exc_info=True)

    error_schema = SendEventsInternalServerErrorSchema(
        code=error_code,
        message=message,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_schema.model_dump(mode="json"),
    )
