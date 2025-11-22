from typing import Literal
from pydantic import BaseModel, Field


class SendEventsResponseSchema(BaseModel):
    """Схема успешного ответа для events endpoint."""

    code: Literal["CREATED"] = Field("CREATED", description="Код статуса")
    message: str = Field(..., description="Сообщение статуса")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "CREATED",
                "message": "Events successfully saved",
            }
        }
