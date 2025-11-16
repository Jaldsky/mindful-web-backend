from typing import Union
from pydantic import Field

from ..error_response_schema import ErrorResponseSchema, ErrorCode
from .event_error_code import EventsErrorCode


class SendEventsInternalServerErrorSchema(ErrorResponseSchema):
    """Схема ошибки 500 Internal Server Error для events endpoint."""

    code: Union[ErrorCode | EventsErrorCode] = Field(..., description="Код ошибки")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "TRANSACTION_FAILED",
                "message": "Database error while saving events",
                "details": None,
                "meta": {
                    "request_id": "aaa5c2b3-1a1b-4612-8ad9-e9e731ea82c0",
                    "timestamp": "2025-11-15T08:38:01.961050Z",
                },
            }
        }
