from ...error_response_schema import ErrorResponseSchema


class DatabaseHealthcheckInternalServerErrorSchema(ErrorResponseSchema):
    """Схема ошибки 500 Internal Server Error для database healthcheck endpoint."""

    class Config:
        json_schema_extra = {
            "example": {
                "code": "HEALTHCHECK_SERVICE_ERROR",
                "message": "Healthcheck service error",
                "details": None,
                "meta": {
                    "request_id": "bbb5c2b3-1a1b-4612-8ad9-e9e731ea82c0",
                    "timestamp": "2025-11-15T08:38:01.961050Z",
                },
            }
        }
