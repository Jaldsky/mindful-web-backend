import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .routes import SEND_EVENTS_PATH, HEALTHCHECK_PATH
from ..schemas import ErrorCode
from ..schemas.general.service_unavailable_schema import ServiceUnavailableSchema

logger = logging.getLogger(__name__)


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


async def service_unavailable_handler(request: Request, exc: Exception) -> JSONResponse:
    """Обработчик для ошибки 503 Service Unavailable.

    Args:
        request: Объект HTTP запроса.
        exc: Исключение.

    Returns:
        JSONResponse.
    """
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
