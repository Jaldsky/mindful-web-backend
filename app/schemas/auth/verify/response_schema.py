from pydantic import BaseModel, Field


class VerifyResponseSchema(BaseModel):
    """Схема ответа на подтверждение email."""

    code: str = Field(default="OK", description="Код ответа")
    message: str = Field(..., description="Сообщение")
