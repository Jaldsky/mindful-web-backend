from typing import Union
from pydantic import Field

from ...error_response_schema import ErrorCode
from ..auth_error_code import AuthErrorCode
from ...general import InternalServerErrorSchema


class ResendCodeInternalServerErrorSchema(InternalServerErrorSchema):
    """Схема ошибки 500 Internal Server Error для resend_code endpoint."""

    code: Union[ErrorCode, AuthErrorCode] = Field(..., description="Код ошибки")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "EMAIL_SEND_FAILED",
                "message": "Failed to send verification email",
                "details": None,
                "meta": {
                    "request_id": "aaa5c2b3-1a1b-4612-8ad9-e9e731ea82c0",
                    "timestamp": "2025-11-15T08:38:01.961050Z",
                },
            }
        }
