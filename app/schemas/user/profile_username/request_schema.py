from typing import Any

from pydantic import BaseModel, Field, field_validator
from pydantic.types import StrictStr


class UpdateUsernameRequestSchema(BaseModel):
    """Схема запроса обновления логина пользователя."""

    username: StrictStr = Field(
        ...,
        description="Новый логин пользователя (3-50 символов, буквы, цифры, подчёркивание)",
    )

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, v: Any) -> Any:
        """Нормализация логина."""
        if not isinstance(v, str):
            return v
        from ....services.auth.normalizers import AuthServiceNormalizers

        return AuthServiceNormalizers.normalize_username(v)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Бизнес-валидация логина (422)."""
        from ....services.auth.validators import AuthServiceValidators

        AuthServiceValidators.validate_username(v)
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "username": "my_username",
            }
        }
