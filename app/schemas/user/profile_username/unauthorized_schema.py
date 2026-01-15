from typing import Union

from pydantic import Field

from ...error_response_schema import ErrorResponseSchema, ErrorCode
from ...auth.auth_error_code import AuthErrorCode


class UpdateUsernameUnauthorizedSchema(ErrorResponseSchema):
    """Схема ошибки 401 Unauthorized для обновления логина пользователя."""

    code: Union[ErrorCode, AuthErrorCode] = Field(..., description="Код ошибки")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "TOKEN_INVALID",
                "message": "Invalid token",
                "details": None,
                "meta": {
                    "request_id": "5d4c75de-7d7d-4f2d-a86f-4d6d00d2d2f7",
                    "timestamp": "2025-11-15T08:38:01.961050Z",
                },
            }
        }
