from typing import Any

from pydantic import BaseModel, Field, field_validator
from pydantic.types import StrictStr


class UpdateEmailRequestSchema(BaseModel):
    """Схема запроса обновления email пользователя."""

    email: StrictStr = Field(
        ...,
        description="Новый email пользователя",
    )

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: Any) -> Any:
        """Нормализация email."""
        if not isinstance(v, str):
            return v
        from ....services.auth.normalizers import AuthServiceNormalizers

        return AuthServiceNormalizers.normalize_email(v)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Бизнес-валидация email (422)."""
        from ....services.auth.validators import AuthServiceValidators

        AuthServiceValidators.validate_email(v)
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "my_username@gmail.com",
            }
        }
