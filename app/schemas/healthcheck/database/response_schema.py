from pydantic import BaseModel, Field


class DatabaseHealthcheckResponseSchema(BaseModel):
    """Схема ответа на проверку доступности базы данных."""

    code: str = Field(..., description="Код статуса")
    message: str = Field(..., description="Сообщение статуса")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "OK",
                "message": "Database is available",
            }
        }
