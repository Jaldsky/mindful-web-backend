from fastapi import status
from fastapi.responses import JSONResponse

from ...schemas import ErrorCode
from ...schemas.healthcheck import HealthcheckMethodNotAllowedSchema


def healthcheck_method_not_allowed_response() -> JSONResponse:
    """Возвращает ответ для ошибки 405 Method Not Allowed для эндпоинта healthcheck.

    Returns:
        JSONResponse с ошибкой 405 Method Not Allowed.
    """
    error_schema = HealthcheckMethodNotAllowedSchema(
        code=ErrorCode.METHOD_NOT_ALLOWED,
        message="Method not allowed. Only GET method is supported for this endpoint.",
    )
    return JSONResponse(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        content=error_schema.model_dump(mode="json"),
    )
