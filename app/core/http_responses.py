from typing import TypeVar

from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..schemas import ErrorCode
from .localizer import localize_key

SchemaT = TypeVar("SchemaT", bound=BaseModel)


def method_not_allowed_response(request: Request, schema_cls: type[SchemaT], *, allowed_method: str) -> JSONResponse:
    """Возвращает стандартный ответ 405 Method Not Allowed для заданной схемы.

    Args:
        request: Объект запроса (для перевода сообщения).
        schema_cls: Класс pydantic-схемы ошибки.
        allowed_method: Разрешённый HTTP метод.

    Returns:
        JSONResponse с ошибкой 405 Method Not Allowed.
    """
    fallback = "Method not allowed. Only {allowed_method} method is supported for this endpoint."
    message = localize_key(request, "general.method_not_allowed_only_method", fallback)
    if "{allowed_method}" in message:
        message = message.format(allowed_method=allowed_method)

    error_schema = schema_cls(code=ErrorCode.METHOD_NOT_ALLOWED, message=message)
    return JSONResponse(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        content=error_schema.model_dump(mode="json"),
    )
