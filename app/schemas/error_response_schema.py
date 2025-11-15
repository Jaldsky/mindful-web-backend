from typing import Any
from pydantic import BaseModel, Field

from .common_meta_schema import CommonMetaSchema
from ..common.common import StringEnum


class ErrorCode(StringEnum):
    """Коды ошибок."""

    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_USER_ID = "INVALID_USER_ID"
    TIMESTAMP_ERROR = "TIMESTAMP_ERROR"

    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"

    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    CONFLICT = "CONFLICT"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"


class ErrorDetailData(BaseModel):
    """Схема для детализации ошибки валидации."""

    field: str = Field(..., description="Поле с ошибкой")
    message: str = Field(..., description="Локальное сообщение об ошибке")
    value: Any | None = Field(None, description="Значение аргумента")


class ErrorResponseSchema(BaseModel):
    """Схема ошибки с метаданными для трейсинга."""

    code: ErrorCode = Field(..., description="Код ошибки")
    message: str = Field(..., description="Общее сообщение об ошибке")
    details: list[ErrorDetailData] | None = Field(None, description="Детали ошибки")
    meta: CommonMetaSchema | None = Field(default_factory=CommonMetaSchema, description="Метаданные запроса")
