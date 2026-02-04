from pydantic import BaseModel, Field


class RegisterResponseSchema(BaseModel):
    """Схема ответа на регистрацию."""

    code: str = Field(default="CREATED", description="Код ответа")
    message: str = Field(..., description="Текст сообщения")
    user_id: str = Field(..., description="Идентификатор пользователя")
    email: str = Field(..., description="Email для подтверждения")
