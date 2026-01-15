from typing import Union

from pydantic import Field

from ...error_response_schema import ErrorResponseSchema, ErrorCode
from ...auth.auth_error_code import AuthErrorCode


class UpdateUsernameUnprocessableEntitySchema(ErrorResponseSchema):
    """Схема ошибки 422 Unprocessable Entity для обновления логина пользователя."""

    code: Union[ErrorCode, AuthErrorCode] = Field(..., description="Код ошибки")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "INVALID_USERNAME_FORMAT",
                "message": "Username length is invalid",
                "details": None,
                "meta": {
                    "request_id": "5d4c75de-7d7d-4f2d-a86f-4d6d00d2d2f7",
                    "timestamp": "2025-11-15T08:38:01.961050Z",
                },
            }
        }
