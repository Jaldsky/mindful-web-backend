from pydantic import BaseModel, Field


class RefreshResponseSchema(BaseModel):
    """Схема ответа на обновление токена."""

    code: str = Field(default="OK", description="Код ответа")
    message: str = Field(default="Token refreshed successfully", description="Сообщение")
    access_token: str = Field(..., description="Новый Access токен")
    refresh_token: str = Field(..., description="Новый Refresh токен")
