from ...error_response_schema import ErrorResponseSchema


class DatabaseHealthcheckServiceUnavailableSchema(ErrorResponseSchema):
    """Схема ошибки 503 Service Unavailable для database healthcheck endpoint."""

    class Config:
        json_schema_extra = {
            "example": {
                "code": "SERVICE_UNAVAILABLE",
                "message": "Service is unavailable",
                "details": None,
                "meta": {
                    "request_id": "ccc5c2b3-1a1b-4612-8ad9-e9e731ea82c0",
                    "timestamp": "2025-11-15T08:38:01.961050Z",
                },
            }
        }
