from pydantic import BaseModel, Field


class LogoutResponseSchema(BaseModel):
    """Схема ответа на выход пользователя из системы."""

    code: str = Field(default="OK", description="Код ответа")
    message: str = Field(..., description="Сообщение")
