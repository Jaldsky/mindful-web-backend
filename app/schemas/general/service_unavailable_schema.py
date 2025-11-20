from app.schemas.error_response_schema import ErrorResponseSchema


class ServiceUnavailableSchema(ErrorResponseSchema):
    """Схема ошибки 503 Service Unavailable."""

    class Config:
        json_schema_extra = {
            "example": {
                "code": "SERVICE_UNAVAILABLE",
                "message": "Service is not available",
                "details": None,
                "meta": {
                    "request_id": "aaa5c2b3-1a1b-4612-8ad9-e9e731ea82c0",
                    "timestamp": "2025-11-15T08:38:01.961050Z",
                },
            }
        }
