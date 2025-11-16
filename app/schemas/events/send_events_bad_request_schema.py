from typing import Union
from pydantic import Field

from ..error_response_schema import ErrorResponseSchema, ErrorCode
from .event_error_code import EventsErrorCode


class SendEventsBadRequestSchema(ErrorResponseSchema):
    """Схема ошибки 400 Bad Request для events endpoint."""

    code: Union[ErrorCode | EventsErrorCode] = Field(..., description="Код ошибки")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "INVALID_USER_ID",
                "message": "Invalid X-User-ID: must be a valid UUID4 string",
                "details": [
                    {
                        "field": "data",
                        "message": "Field required",
                        "value": None,
                    }
                ],
                "meta": {
                    "request_id": "aaa5c2b3-1a1b-4612-8ad9-e9e731ea82c0",
                    "timestamp": "2025-11-15T08:38:01.961050Z",
                },
            }
        }
