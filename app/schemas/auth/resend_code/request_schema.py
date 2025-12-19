from pydantic import BaseModel, Field, EmailStr


class ResendCodeRequestSchema(BaseModel):
    """Схема запроса повторной отправки кода подтверждения."""

    email: EmailStr = Field(
        ...,
        description="Email пользователя",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "email": "my_username@gmail.com",
            }
        }
