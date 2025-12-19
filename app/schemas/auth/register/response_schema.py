from pydantic import BaseModel, Field


class RegisterResponseSchema(BaseModel):
    """Схема ответа на регистрацию."""

    code: str = Field(default="CREATED", description="Код ответа")
    message: str = Field(
        default="Код подтверждения отправлен на email",
        description="Текст сообщения",
    )
    user_id: str = Field(..., description="Идентификатор пользователя")
    email: str = Field(..., description="Email для подтверждения")
