from ..error_response_schema import ErrorResponseSchema


class InternalServerErrorSchema(ErrorResponseSchema):
    """Схема ошибки 500 Internal Server Error."""

    class Config:
        json_schema_extra = {
            "example": {
                "code": "INTERNAL_ERROR",
                "message": "Internal server error",
                "details": None,
                "meta": {
                    "request_id": "aaa5c2b3-1a1b-4612-8ad9-e9e731ea82c0",
                    "timestamp": "2025-11-15T08:38:01.961050Z",
                },
            }
        }
