from pydantic import BaseModel, Field


class ProfileDataSchema(BaseModel):
    """Схема данных профиля пользователя."""

    username: str | None = Field(None, description="Логин пользователя")
    email: str | None = Field(None, description="Email пользователя")


class ProfileResponseSchema(BaseModel):
    """Схема успешного ответа user-сервиса (профиль / обновление профиля)."""

    code: str = Field(default="OK", description="Код ответа")
    message: str = Field(..., description="Сообщение")
    data: ProfileDataSchema = Field(..., description="Данные профиля пользователя")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "OK",
                "message": "Profile loaded",
                "data": {
                    "username": "testuser",
                    "email": "test@example.com",
                },
            }
        }
