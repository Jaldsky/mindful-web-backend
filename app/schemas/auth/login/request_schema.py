from pydantic import BaseModel, Field


class LoginRequestSchema(BaseModel):
    """Схема запроса авторизации."""

    username: str = Field(
        ...,
        description="Логин пользователя",
    )
    password: str = Field(
        ...,
        description="Пароль",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "username": "my_username",
                "password": "SecurePass123",
            }
        }
