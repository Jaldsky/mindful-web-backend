from typing import Any

from pydantic import BaseModel, Field, field_validator
from pydantic.types import StrictStr


class RegisterRequestSchema(BaseModel):
    """Схема запроса регистрации пользователя."""

    username: StrictStr = Field(
        ...,
        description="Логин пользователя (3-50 символов, буквы, цифры, подчёркивание)",
    )
    email: StrictStr = Field(
        ...,
        description="Email пользователя",
    )
    password: StrictStr = Field(
        ...,
        description="Пароль (минимум 8 символов, буквы и цифры)",
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

    @field_validator("password", mode="before")
    @classmethod
    def normalize_password(cls, v: Any) -> Any:
        """Нормализация пароля."""
        if not isinstance(v, str):
            return v
        from ....services.auth.normalizers import AuthServiceNormalizers

        return AuthServiceNormalizers.normalize_password(v)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Бизнес-валидация пароля (422)."""
        from ....services.auth.validators import AuthServiceValidators

        AuthServiceValidators.validate_password(v)
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "username": "my_username",
                "email": "my_username@gmail.com",
                "password": "SecurePass123",
            }
        }
