from pydantic import BaseModel, Field


class ProfileDataSchema(BaseModel):
    """Схема данных профиля пользователя."""

    username: str | None = Field(None, description="Логин пользователя")
    email: str | None = Field(None, description="Email пользователя")


class ProfileResponseSchema(BaseModel):
    """Схема ответа на получение профиля пользователя."""

    data: ProfileDataSchema = Field(..., description="Данные профиля пользователя")

    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "username": "testuser",
                    "email": "test@example.com",
                },
            }
        }
