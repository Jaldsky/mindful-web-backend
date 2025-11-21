from ..error_response_schema import ErrorResponseSchema


class UnprocessableEntitySchema(ErrorResponseSchema):
    """Схема ошибки 422 Unprocessable Entity."""

    class Config:
        json_schema_extra = {
            "example": {
                "code": "BUSINESS_VALIDATION_ERROR",
                "message": "Business validation failed",
                "details": [
                    {
                        "field": "field_name",
                        "message": "Validation error message",
                        "value": "invalid_value",
                    }
                ],
                "meta": {
                    "request_id": "aaa5c2b3-1a1b-4612-8ad9-e9e731ea82c0",
                    "timestamp": "2025-11-15T08:38:01.961050Z",
                },
            }
        }
