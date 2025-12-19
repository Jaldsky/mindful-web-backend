from pydantic import BaseModel, Field, field_validator, EmailStr


class VerifyRequestSchema(BaseModel):
    """Схема запроса подтверждения email."""

    email: EmailStr = Field(
        ...,
        description="Email пользователя",
    )
    code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="6-значный код подтверждения",
    )

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Валидация кода."""
        v = v.strip()
        if not v.isdigit():
            raise ValueError("Verification code must contain only digits")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "my_username@gmail.com",
                "code": "123456",
            }
        }
