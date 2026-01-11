import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse

from ....common.http_responses import method_not_allowed_response
from ....schemas import ErrorCode, ErrorDetailData
from ....schemas.analytics import (
    AnalyticsErrorCode,
    AnalyticsUsageUnprocessableEntitySchema,
    AnalyticsUsageInternalServerErrorSchema,
    AnalyticsUsageMethodNotAllowedSchema,
)
from .exceptions import UsageServerException, UsageBusinessValidationException

logger = logging.getLogger(__name__)


def usage_method_not_allowed_response() -> JSONResponse:
    """Функция возврата ответа 405 Method Not Allowed для POST /usage

    Returns:
        JSONResponse с ошибкой 405 Method Not Allowed.
    """
    return method_not_allowed_response(AnalyticsUsageMethodNotAllowedSchema, allowed_method="GET")


def usage_business_validation_exception_response(
    request: Request, exc: UsageBusinessValidationException
) -> JSONResponse:
    """Возвращает ответ для ошибки 422 Unprocessable Entity для эндпоинта usage.

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
        case "InvalidDateFormatException":
            error_code = AnalyticsErrorCode.INVALID_DATE_FORMAT
            field_name = "from/to"
            if "'from' date" in message.lower():
                field_name = "from"
            elif "'to' date" in message.lower():
                field_name = "to"
            error_details = [
                ErrorDetailData(
                    field=field_name,
                    message=message,
                    value=None,
                )
            ]
        case "InvalidTimeRangeException":
            error_code = AnalyticsErrorCode.INVALID_TIME_RANGE
            error_details = [
                ErrorDetailData(
                    field="from/to",
                    message=message,
                    value=None,
                )
            ]
        case "InvalidPageException":
            error_code = AnalyticsErrorCode.INVALID_PAGE
            error_details = [
                ErrorDetailData(
                    field="page",
                    message=message,
                    value=None,
                )
            ]
        case "InvalidPageSizeException":
            error_code = AnalyticsErrorCode.INVALID_PAGE_SIZE
            error_details = [
                ErrorDetailData(
                    field="page_size",
                    message=message,
                    value=None,
                )
            ]
        case "InvalidEventTypeException":
            error_code = AnalyticsErrorCode.INVALID_EVENT_TYPE
            error_details = [
                ErrorDetailData(
                    field="event_type",
                    message=message,
                    value=None,
                )
            ]

    logger.warning(f"Usage validation error: {message}")

    error_schema = AnalyticsUsageUnprocessableEntitySchema(
        code=error_code,
        message=message,
        details=error_details,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_schema.model_dump(mode="json"),
    )


def usage_server_exception_response(request: Request, exc: UsageServerException) -> JSONResponse:
    """Возвращает ответ для ошибки 500 Internal Server Error.

    Args:
        request: Объект HTTP запроса.
        exc: Исключение.

    Returns:
        JSONResponse с ошибкой 500 Internal Server Error.
    """
    message = str(exc)
    error_code = ErrorCode.INTERNAL_ERROR

    logger.error(f"Usage server error: {message}", exc_info=True)

    error_schema = AnalyticsUsageInternalServerErrorSchema(
        code=error_code,
        message=message,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_schema.model_dump(mode="json"),
    )
