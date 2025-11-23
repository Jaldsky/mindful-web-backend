import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .routes import SEND_EVENTS_PATH, HEALTHCHECK_PATH
from ..schemas import ErrorCode, ErrorDetailData

logger = logging.getLogger(__name__)


async def events_service_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Обработчик для всех исключений сервиса событий.

    Args:
        request: Объект HTTP запроса.
        exc: Исключение EventsServiceException или его подкласс.

    Returns:
        JSONResponse.
    """
    from ..services.events.send_events.exceptions import (
        EventsBusinessValidationException,
        EventsServerException,
    )
    from ..services.events.send_events.http_handler import (
        send_events_business_validation_exception_response,
        send_events_server_exception_response,
    )
    from ..schemas.general import UnprocessableEntitySchema, InternalServerErrorSchema
    from .routes import SEND_EVENTS_PATH

    if str(request.url.path) == SEND_EVENTS_PATH:
        if isinstance(exc, EventsBusinessValidationException):
            return send_events_business_validation_exception_response(request, exc)
        elif isinstance(exc, EventsServerException):
            return send_events_server_exception_response(request, exc)

    if isinstance(exc, EventsBusinessValidationException):
        error_schema = UnprocessableEntitySchema(
            code=ErrorCode.BUSINESS_VALIDATION_ERROR,
            message=str(exc),
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_schema.model_dump(mode="json"),
        )
    else:
        error_schema = InternalServerErrorSchema(
            code=ErrorCode.INTERNAL_ERROR,
            message=str(exc),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_schema.model_dump(mode="json"),
        )


async def usage_service_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Обработчик для всех исключений сервиса аналитики использования.

    Args:
        request: Объект HTTP запроса.
        exc: Исключение UsageServiceException или его подкласс.

    Returns:
        JSONResponse.
    """
    from ..services.analytics.usage.exceptions import (
        UsageBusinessValidationException,
        UsageServerException,
    )
    from ..services.analytics.usage.http_handler import (
        usage_business_validation_exception_response,
        usage_server_exception_response,
    )
    from ..schemas.general import UnprocessableEntitySchema, InternalServerErrorSchema

    if "/analytics/usage" in str(request.url.path):
        if isinstance(exc, UsageBusinessValidationException):
            return usage_business_validation_exception_response(request, exc)
        elif isinstance(exc, UsageServerException):
            return usage_server_exception_response(request, exc)

    if isinstance(exc, UsageBusinessValidationException):
        error_schema = UnprocessableEntitySchema(
            code=ErrorCode.BUSINESS_VALIDATION_ERROR,
            message=str(exc),
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_schema.model_dump(mode="json"),
        )
    else:
        error_schema = InternalServerErrorSchema(
            code=ErrorCode.INTERNAL_ERROR,
            message=str(exc),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_schema.model_dump(mode="json"),
        )


async def bad_request_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Обработчик для ошибки 400 Bad Request.

    Args:
        request: Объект HTTP запроса.
        exc: Исключение.

    Returns:
        JSONResponse.
    """
    from ..schemas.general import BadRequestSchema

    error_details = None
    if isinstance(exc, RequestValidationError):
        error_details = [
            ErrorDetailData(
                field=".".join(str(loc) for loc in err.get("loc", ())),
                message=err.get("msg", ""),
                value=err.get("input"),
            )
            for err in exc.errors()
        ] or None

    error_schema = BadRequestSchema(
        code=ErrorCode.VALIDATION_ERROR, message="Payload validation failed", details=error_details
    )

    logger.warning(f"Validation error: {error_schema.message}")

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_schema.model_dump(mode="json"),
    )


async def method_not_allowed_handler(request: Request, exc: Exception) -> JSONResponse:
    """Обработчик для ошибки 405 Method Not Allowed.

    Args:
        request: Объект HTTP запроса.
        exc: Исключение.

    Returns:
        JSONResponse.
    """
    from ..services.healthcheck import healthcheck_method_not_allowed_response
    from ..services.events.send_events.http_handler import send_events_method_not_allowed_response

    if str(request.url.path) == HEALTHCHECK_PATH:
        return healthcheck_method_not_allowed_response()

    if str(request.url.path) == SEND_EVENTS_PATH:
        return send_events_method_not_allowed_response()

    detail = "Method not allowed"
    if isinstance(exc, StarletteHTTPException) and exc.detail:
        detail = str(exc.detail)

    return JSONResponse(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        content={"detail": detail},
    )


async def unprocessable_entity_handler(request: Request, exc: Exception) -> JSONResponse:
    """Обработчик для ошибки 422 Unprocessable Entity.

    Args:
        request: Объект HTTP запроса.
        exc: Исключение.

    Returns:
        JSONResponse.
    """
    from ..schemas.general import UnprocessableEntitySchema

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    message = "Business validation failed"
    error_code = ErrorCode.BUSINESS_VALIDATION_ERROR
    error_details = None

    if isinstance(exc, StarletteHTTPException) and exc.status_code == status_code:
        if isinstance(exc.detail, dict):
            return JSONResponse(status_code=status_code, content=exc.detail)
        if exc.detail:
            message = str(exc.detail)
    elif hasattr(exc, "__str__"):
        message = str(exc)

    logger.warning(f"Unprocessable entity: {message}")

    error_schema = UnprocessableEntitySchema(
        code=error_code,
        message=message,
        details=error_details,
    )
    return JSONResponse(
        status_code=status_code,
        content=error_schema.model_dump(mode="json"),
    )


async def internal_server_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Обработчик для ошибки 500 Internal Server Error.

    Args:
        request: Объект HTTP запроса.
        exc: Исключение.

    Returns:
        JSONResponse.
    """
    from sqlalchemy.exc import ArgumentError, SQLAlchemyError
    from ..db.exceptions import DatabaseManagerException
    from ..schemas.general import InternalServerErrorSchema

    message = "Internal server error"
    error_code = ErrorCode.INTERNAL_ERROR

    if isinstance(exc, (DatabaseManagerException, ArgumentError, SQLAlchemyError)):
        error_code = ErrorCode.DATABASE_ERROR
        message = "Database error"

    if isinstance(exc, StarletteHTTPException) and exc.detail:
        message = str(exc.detail)
    elif hasattr(exc, "__str__"):
        message = str(exc)

    logger.error(f"Internal server error: {message}", exc_info=True)

    error_schema = InternalServerErrorSchema(
        code=error_code,
        message=message,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_schema.model_dump(mode="json"),
    )


async def celery_task_timeout_handler(request: Request, exc: Exception) -> JSONResponse:
    """Обработчик для таймаута выполнения Celery задачи (202 Accepted).

    Args:
        request: Объект HTTP запроса.
        exc: Исключение OrchestratorTimeoutException.

    Returns:
        JSONResponse с кодом 202 Accepted.
    """
    from app.services.scheduler.exceptions import OrchestratorTimeoutException
    from ..schemas.analytics import AnalyticsUsageResponseAcceptedSchema

    if isinstance(exc, OrchestratorTimeoutException):
        accepted = AnalyticsUsageResponseAcceptedSchema(task_id=exc.task_id)
        logger.info(f"Celery task timeout, returning 202 Accepted for task {exc.task_id}")
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=accepted.model_dump(mode="json"),
        )

    # Fallback
    from ..schemas.analytics import AnalyticsUsageResponseAcceptedSchema

    accepted = AnalyticsUsageResponseAcceptedSchema(task_id="unknown")
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content=accepted.model_dump(mode="json"),
    )


async def celery_broker_unavailable_handler(request: Request, exc: Exception) -> JSONResponse:
    """Обработчик для недоступности Celery брокера (503 Service Unavailable).

    Args:
        request: Объект HTTP запроса.
        exc: Исключение OrchestratorBrokerUnavailableException.

    Returns:
        JSONResponse с кодом 503 Service Unavailable.
    """
    from app.services.scheduler.exceptions import OrchestratorBrokerUnavailableException
    from ..schemas.general.service_unavailable_schema import ServiceUnavailableSchema

    message = "Analytics broker is not available"
    if isinstance(exc, OrchestratorBrokerUnavailableException):
        message = exc.message

    logger.error(f"Celery broker unavailable: {message}")

    error_schema = ServiceUnavailableSchema(
        code=ErrorCode.SERVICE_UNAVAILABLE,
        message=message,
    )
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=error_schema.model_dump(mode="json"),
    )


async def service_unavailable_handler(request: Request, exc: Exception) -> JSONResponse:
    """Обработчик для ошибки 503 Service Unavailable.

    Args:
        request: Объект HTTP запроса.
        exc: Исключение.

    Returns:
        JSONResponse.
    """
    from ..schemas.general.service_unavailable_schema import ServiceUnavailableSchema

    message = "Service is not available"
    if isinstance(exc, StarletteHTTPException) and exc.detail:
        message = str(exc.detail)

    logger.error(f"Service unavailable: {message}")

    error_schema = ServiceUnavailableSchema(
        code=ErrorCode.SERVICE_UNAVAILABLE,
        message=message,
    )
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=error_schema.model_dump(mode="json"),
    )
