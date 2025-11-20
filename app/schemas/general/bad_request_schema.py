from ..error_response_schema import ErrorResponseSchema


class BadRequestSchema(ErrorResponseSchema):
    """Схема ошибки 400 Bad Request."""

    class Config:
        json_schema_extra = {
            "example": {
                "code": "VALIDATION_ERROR",
                "message": "Payload validation failed",
                "details": [
                    {
                        "field": "data[].timestamp",
                        "message": "Input should be a valid datetime, invalid character detected",
                        "value": "my-str",
                    }
                ],
                "meta": {
                    "request_id": "aaa5c2b3-1a1b-4612-8ad9-e9e731ea82c0",
                    "timestamp": "2025-11-15T08:38:01.961050Z",
                },
            }
        }
