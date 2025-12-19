from pydantic import BaseModel, Field


class RefreshRequestSchema(BaseModel):
    """Схема запроса обновления токена."""

    refresh_token: str = Field(..., description="Refresh токен")
