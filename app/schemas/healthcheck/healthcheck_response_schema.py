from pydantic import BaseModel, Field


class HealthcheckResponseSchema(BaseModel):
    code: str = Field(..., description="Код статуса")
    message: str = Field(..., description="Сообщение статуса")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "OK",
                "message": "Service is available",
            }
        }
