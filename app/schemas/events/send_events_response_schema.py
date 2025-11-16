from pydantic import BaseModel, Field


class SendEventsResponseSchema(BaseModel):
    """Схема успешного ответа для events endpoint."""

    code: str = Field(..., description="Код статуса")
    message: str = Field(..., description="Сообщение статуса")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "CREATED",
                "message": "Events successfully saved",
            }
        }
