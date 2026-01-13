from typing import Literal
from pydantic import BaseModel, Field


class SaveEventsResponseSchema(BaseModel):
    """Схема успешного ответа для events/save endpoint."""

    code: Literal["CREATED"] = Field("CREATED", description="Код статуса")
    message: str = Field(..., description="Сообщение статуса")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "CREATED",
                "message": "Events successfully saved",
            }
        }
