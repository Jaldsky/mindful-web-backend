from typing import Any

from pydantic import BaseModel, Field, field_validator
from pydantic.types import StrictStr


class LoginRequestSchema(BaseModel):
    """Схема запроса авторизации."""

    username: StrictStr = Field(
        ...,
        description="Логин пользователя",
    )
    password: StrictStr = Field(
        ...,
        description="Пароль",
    )

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, v: Any) -> Any:
        """Нормализация username."""
        if not isinstance(v, str):
            return v
        from ....services.auth.normalizers import AuthServiceNormalizers

        return AuthServiceNormalizers.normalize_username(v)

    @field_validator("password", mode="before")
    @classmethod
    def normalize_password(cls, v: Any) -> Any:
        """Нормализация password."""
        if not isinstance(v, str):
            return v
        from ....services.auth.normalizers import AuthServiceNormalizers

        return AuthServiceNormalizers.normalize_password(v)

    class Config:
        json_schema_extra = {
            "example": {
                "username": "my_username",
                "password": "SecurePass123",
            }
        }
