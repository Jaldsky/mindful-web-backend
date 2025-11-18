from typing import Union
from pydantic import Field

from ..error_response_schema import ErrorResponseSchema, ErrorCode
from .event_error_code import EventsErrorCode


class SendEventsUnprocessableEntitySchema(ErrorResponseSchema):
    """Схема ошибки 422 Unprocessable Entity для events endpoint."""

    code: Union[ErrorCode | EventsErrorCode] = Field(..., description="Код ошибки")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "INVALID_EVENT_TYPE",
                "message": "Event must be either active or inactive",
                "details": [
                    {
                        "field": "data[].event",
                        "message": "Event must be either active or inactive",
                        "value": "focus",
                    }
                ],
                "meta": {
                    "request_id": "5d4c75de-7d7d-4f2d-a86f-4d6d00d2d2f7",
                    "timestamp": "2025-11-15T08:38:01.961050Z",
                },
            }
        }
