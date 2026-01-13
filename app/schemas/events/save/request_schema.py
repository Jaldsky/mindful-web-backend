from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from ....schemas import CommonMetaSchema


class SaveEventData(BaseModel):
    """Схема данных одного события."""

    event: str = Field(
        ...,
        description="Тип события внимания: active - пользователь перешёл на вкладку, inactive - покинул вкладку",
    )
    domain: str = Field(..., min_length=1, description="Домен")
    timestamp: datetime = Field(..., description="Временная метка события в формате ISO 8601 UTC.")

    @field_validator("event", mode="before")
    @classmethod
    def normalize_event_type(cls, v: Any) -> Any:
        """Нормализация event."""
        if not isinstance(v, str):
            return v
        from ....services.events.normalizers import EventsServiceNormalizers

        return EventsServiceNormalizers.normalize_event_type(v)

    @field_validator("event")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        """Бизнес-валидация event (422)."""
        from ....services.events.validators import EventsServiceValidators

        EventsServiceValidators.validate_event_type(v)
        return v

    @field_validator("domain", mode="before")
    @classmethod
    def normalize_domain(cls, v: Any) -> Any:
        """Нормализация домена."""
        if not isinstance(v, str):
            return v
        from ....services.events.normalizers import EventsServiceNormalizers

        return EventsServiceNormalizers.normalize_domain(v)

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        """Бизнес-валидация домена (422)."""
        from ....services.events.validators import EventsServiceValidators

        EventsServiceValidators.validate_domain(v)
        return v

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp_not_in_future(cls, v: datetime) -> datetime:
        """Бизнес-валидация timestamp (422)."""
        from ....services.events.validators import EventsServiceValidators

        EventsServiceValidators.validate_timestamp_not_in_future(v)
        return v


class SaveEventsRequestSchema(BaseModel):
    """Схема запроса для сохранения событий."""

    data: list[SaveEventData] = Field(
        ...,
        description="Список событий внимания",
    )
    meta: CommonMetaSchema | None = Field(default_factory=CommonMetaSchema, description="Метаданные запроса")

    @field_validator("data")
    @classmethod
    def validate_data_list(cls, v: list[SaveEventData]) -> list[SaveEventData]:
        """Валидация списка событий."""
        from ....services.events.validators import EventsServiceValidators

        EventsServiceValidators.validate_events_list(v)
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "data": [
                    {
                        "event": "active",
                        "domain": "reddit.com",
                        "timestamp": "2025-04-05T09:00:00Z",
                    },
                    {
                        "event": "inactive",
                        "domain": "reddit.com",
                        "timestamp": "2025-04-05T09:05:22Z",
                    },
                ]
            }
        }
