import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..exceptions import AppException
from .routes import (
    ANALYTICS_USAGE_PATH,
    HEALTHCHECK_PATH,
    SEND_EVENTS_PATH,
    AUTH_LOGIN_PATH,
    AUTH_REFRESH_PATH,
    AUTH_REGISTER_PATH,
    AUTH_RESEND_CODE_PATH,
    AUTH_VERIFY_PATH,
)
from ..schemas import ErrorCode, ErrorDetailData
from ..schemas.general import UnprocessableEntitySchema, InternalServerErrorSchema, BadRequestSchema
from ..schemas.general.service_unavailable_schema import ServiceUnavailableSchema

logger = logging.getLogger(__name__)


async def app_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Универсальный обработчик для всех AppException."""
    if not isinstance(exc, AppException):
        error_schema = InternalServerErrorSchema(
            code=ErrorCode.INTERNAL_ERROR, message="Unknown exception type handled by app_exception_handler"
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_schema.model_dump(mode="json"),
        )

    if exc.status_code >= 500:
        logger.error(f"App error: {exc.message}", exc_info=True)
    else:
        logger.warning(f"App warning: {exc.message}")

    return JSONResponse(
        status_code=exc.status_code,
        content=exc.get_response_content(),
    )


async def bad_request_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Обработчик для ошибки 400 Bad Request."""

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
    """Обработчик для ошибки 405 Method Not Allowed."""
    from ..services.healthcheck import healthcheck_method_not_allowed_response
    from ..services.events.send_events.http_handler import send_events_method_not_allowed_response
    from ..services.analytics.usage.http_handler import usage_method_not_allowed_response
    from ..services.auth.http_handler import (
        auth_login_method_not_allowed_response,
        auth_refresh_method_not_allowed_response,
        auth_register_method_not_allowed_response,
        auth_resend_code_method_not_allowed_response,
        auth_verify_method_not_allowed_response,
    )

    if str(request.url.path) == HEALTHCHECK_PATH:
        return healthcheck_method_not_allowed_response()

    if str(request.url.path) == SEND_EVENTS_PATH:
        return send_events_method_not_allowed_response()

    if str(request.url.path) == ANALYTICS_USAGE_PATH:
        return usage_method_not_allowed_response()

    if str(request.url.path) == AUTH_REGISTER_PATH:
        return auth_register_method_not_allowed_response()

    if str(request.url.path) == AUTH_LOGIN_PATH:
        return auth_login_method_not_allowed_response()

    if str(request.url.path) == AUTH_REFRESH_PATH:
        return auth_refresh_method_not_allowed_response()

    if str(request.url.path) == AUTH_VERIFY_PATH:
        return auth_verify_method_not_allowed_response()

    if str(request.url.path) == AUTH_RESEND_CODE_PATH:
        return auth_resend_code_method_not_allowed_response()

    detail = "Method not allowed"
    if isinstance(exc, StarletteHTTPException) and exc.detail:
        detail = str(exc.detail)

    return JSONResponse(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        content={"detail": detail},
    )


async def unprocessable_entity_handler(request: Request, exc: Exception) -> JSONResponse:
    """Обработчик для ошибки 422 Unprocessable Entity (Starlette)."""
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
    """Обработчик для ошибки 500 Internal Server Error (Generic)."""
    from sqlalchemy.exc import ArgumentError, SQLAlchemyError
    from ..db.exceptions import DatabaseManagerException

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


async def service_unavailable_handler(request: Request, exc: Exception) -> JSONResponse:
    """Обработчик для ошибки 503 Service Unavailable."""
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
