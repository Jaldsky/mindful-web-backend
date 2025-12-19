from pydantic import BaseModel, Field


class LoginResponseSchema(BaseModel):
    """Схема ответа на авторизацию."""

    code: str = Field(default="OK", description="Код ответа")
    message: str = Field(default="Login successful", description="Сообщение")
    access_token: str = Field(..., description="Access токен")
    refresh_token: str = Field(..., description="Refresh токен")
