import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class CommonMetaSchema(BaseModel):
    """Общая схема метаданных запроса."""

    request_id: str | None = Field(default_factory=lambda: str(uuid.uuid4()), description="Уникальный ID запроса")
    timestamp: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="Время создания запроса"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "request_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2025-01-15T10:30:00Z",
            }
        }
