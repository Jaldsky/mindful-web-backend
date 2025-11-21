from typing import Any
from pydantic import BaseModel, Field

from .common_meta_schema import CommonMetaSchema
from ..common.common import StringEnum


class ErrorCode(StringEnum):
    """Общие коды ошибок."""

    VALIDATION_ERROR = "VALIDATION_ERROR"  # Ошибка 400
    UNAUTHORIZED = "UNAUTHORIZED"  # Ошибка 401
    FORBIDDEN = "FORBIDDEN"  # Ошибка 403
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"  # Ошибка 404
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"  # Ошибка 405
    BUSINESS_VALIDATION_ERROR = "BUSINESS_VALIDATION_ERROR"  # Ошибка 422

    INTERNAL_ERROR = "INTERNAL_ERROR"  # Ошибка 500
    DATABASE_ERROR = "DATABASE_ERROR"  # Ошибка 500
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"  # Ошибка 503


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
