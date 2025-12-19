import re
from pydantic import BaseModel, Field, field_validator, EmailStr

from ....services.auth.exceptions import (
    InvalidUsernameFormatException,
    InvalidPasswordFormatException,
)


class RegisterRequestSchema(BaseModel):
    """Схема запроса регистрации пользователя."""

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Логин пользователя (3-50 символов, буквы, цифры, подчёркивание)",
    )
    email: EmailStr = Field(
        ...,
        description="Email пользователя",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Пароль (минимум 8 символов, буквы и цифры)",
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Валидация логина."""
        v = v.strip().lower()
        if not re.match(r"^[a-z0-9_]+$", v):
            raise InvalidUsernameFormatException(
                "Username must contain only lowercase letters, numbers, and underscores"
            )
        if v.startswith("_") or v.endswith("_"):
            raise InvalidUsernameFormatException("Username cannot start or end with underscore")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Валидация пароля."""
        if not re.search(r"[a-zA-Z]", v):
            raise InvalidPasswordFormatException("Password must contain at least one letter")
        if not re.search(r"\d", v):
            raise InvalidPasswordFormatException("Password must contain at least one digit")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "username": "my_username",
                "email": "my_username@gmail.com",
                "password": "SecurePass123",
            }
        }
