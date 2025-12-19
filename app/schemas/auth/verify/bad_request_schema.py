from typing import Union
from pydantic import Field

from ...error_response_schema import ErrorResponseSchema, ErrorCode
from ..auth_error_code import AuthErrorCode


class VerifyBadRequestSchema(ErrorResponseSchema):
    """Схема ошибки 400 Bad Request для verify endpoint."""

    code: Union[ErrorCode, AuthErrorCode] = Field(..., description="Код ошибки")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "INVALID_VERIFICATION_CODE",
                "message": "Verification code must contain only digits",
                "details": [
                    {
                        "field": "code",
                        "message": "Verification code must contain only digits",
                        "value": "abc123",
                    }
                ],
                "meta": {
                    "request_id": "5d4c75de-7d7d-4f2d-a86f-4d6d00d2d2f7",
                    "timestamp": "2025-11-15T08:38:01.961050Z",
                },
            }
        }
