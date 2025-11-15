from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .routes import HEALTHCHECK_PATH
from ..schemas import ErrorCode
from ..schemas.healthcheck import HealthcheckMethodNotAllowedSchema


async def method_not_allowed_handler(request: Request, exc: Exception) -> JSONResponse:
    """Обработчик для ошибки 405 Method Not Allowed.

    Args:
        request: Объект HTTP запроса.
        exc: Исключение.

    Returns:
        JSONResponse.
    """
    if str(request.url.path) == HEALTHCHECK_PATH:
        error_schema = HealthcheckMethodNotAllowedSchema(
            code=ErrorCode.METHOD_NOT_ALLOWED,
            message="Method not allowed. Only GET method is supported for this endpoint.",
        )
        return JSONResponse(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            content={"detail": error_schema.model_dump(mode="json")},
        )

    detail = "Method not allowed"
    if isinstance(exc, StarletteHTTPException) and exc.detail:
        detail = str(exc.detail)

    return JSONResponse(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        content={"detail": detail},
    )
