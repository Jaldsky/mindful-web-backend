from typing import TypeVar

from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..schemas import ErrorCode

SchemaT = TypeVar("SchemaT", bound=BaseModel)


def method_not_allowed_response(schema_cls: type[SchemaT], *, allowed_method: str) -> JSONResponse:
    """Возвращает стандартный ответ 405 Method Not Allowed для заданной схемы.

    Args:
        schema_cls: Класс pydantic-схемы ошибки.
        allowed_method: Разрешённый HTTP метод.

    Returns:
        JSONResponse с ошибкой 405 Method Not Allowed.
    """
    error_schema = schema_cls(
        code=ErrorCode.METHOD_NOT_ALLOWED,
        message=f"Method not allowed. Only {allowed_method} method is supported for this endpoint.",
    )
    return JSONResponse(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        content=error_schema.model_dump(mode="json"),
    )
