from typing import Any

from pydantic import BaseModel, Field, field_validator
from pydantic.types import StrictStr


class VerifyRequestSchema(BaseModel):
    """Схема запроса подтверждения email."""

    email: StrictStr = Field(
        ...,
        description="Email пользователя",
    )
    code: StrictStr = Field(
        ...,
        description="6-значный код подтверждения",
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

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, v: Any) -> Any:
        """Нормализация кода."""
        if not isinstance(v, str):
            return v
        return (v or "").strip()

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Бизнес-валидация кода (422)."""
        from ....services.auth.validators import AuthServiceValidators

        AuthServiceValidators.validate_verification_code(v)
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "my_username@gmail.com",
                "code": "123456",
            }
        }
