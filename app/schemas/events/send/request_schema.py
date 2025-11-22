import re
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator

from ....schemas import CommonMetaSchema
from ....services.events.send_events.exceptions import (
    EmptyEventsListException,
    InvalidDomainFormatException,
    InvalidDomainLengthException,
    InvalidEventTypeException,
    TimestampInFutureException,
    TooManyEventsException,
)


class SendEventData(BaseModel):
    """Схема данных одного события."""

    event: str = Field(
        ...,
        description="Тип события внимания: active - пользователь перешёл на вкладку, inactive - покинул вкладку",
    )
    domain: str = Field(..., min_length=1, description="Домен")
    timestamp: datetime = Field(..., description="Временная метка события в формате ISO 8601 UTC.")

    @field_validator("event")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        """Валидация event."""
        if v not in ("active", "inactive"):
            raise InvalidEventTypeException("Event must be either active or inactive")
        return v

    @field_validator("domain")
    @classmethod
    def validate_and_normalize_domain(cls, v: str) -> str:
        """Валидация и нормализация домена."""
        if not v or not isinstance(v, str):
            raise InvalidDomainFormatException("Domain must be a non-empty string")

        v = v.strip().lower()
        if not v or "." not in v:
            raise InvalidDomainFormatException("Invalid domain format: must contain at least one dot")
        if v.startswith("http://"):
            v = v[7:]
        elif v.startswith("https://"):
            v = v[8:]
        v = v.split("/")[0].split(":")[0]
        if v.startswith("www."):
            v = v[4:]
        if not v or len(v) > 255:
            raise InvalidDomainLengthException("Domain is invalid or too long after normalization")

        if not re.match(r"^[a-z0-9.-]+$", v):
            raise InvalidDomainFormatException("Domain contains invalid characters")

        if v.startswith(".") or v.endswith(".") or v.startswith("-") or v.endswith("-"):
            raise InvalidDomainFormatException("Domain cannot start or end with dot or dash")

        return v

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp_not_in_future(cls, v: datetime) -> datetime:
        """Валидация timestamp."""
        now = datetime.now(timezone.utc)
        if v > now:
            raise TimestampInFutureException("Timestamp cannot be in the future")
        return v


class SendEventsRequestSchema(BaseModel):
    """Схема запроса для отправки событий."""

    data: list[SendEventData] = Field(
        ...,
        description="Список событий внимания",
    )
    meta: CommonMetaSchema | None = Field(default_factory=CommonMetaSchema, description="Метаданные запроса")

    @field_validator("data")
    @classmethod
    def validate_data_list(cls, v: list[SendEventData]) -> list[SendEventData]:
        """Валидация списка событий."""
        if not v or len(v) == 0:
            raise EmptyEventsListException("Events list cannot be empty")
        if len(v) > 100:
            raise TooManyEventsException("Events list cannot contain more than 100 events")
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
