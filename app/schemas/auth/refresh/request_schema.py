from typing import Any

from pydantic import BaseModel, Field, field_validator
from pydantic.types import StrictStr


class RefreshRequestSchema(BaseModel):
    """Схема запроса обновления токена."""

    refresh_token: StrictStr = Field(..., description="Refresh токен")

    @field_validator("refresh_token", mode="before")
    @classmethod
    def normalize_refresh_token(cls, v: Any) -> Any:
        """Нормализация refresh token."""
        if not isinstance(v, str):
            return v
        from ....services.auth.normalizers import AuthServiceNormalizers

        return AuthServiceNormalizers.normalize_jwt_token(v)

    @field_validator("refresh_token")
    @classmethod
    def validate_refresh_token(cls, v: str) -> str:
        """Валидация наличия токена обновления (401)."""
        from ....services.auth.validators import AuthServiceValidators

        AuthServiceValidators.validate_jwt_token(v)
        return v
