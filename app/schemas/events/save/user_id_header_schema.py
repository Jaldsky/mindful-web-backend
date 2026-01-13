from uuid import uuid4
from pydantic import BaseModel, Field, field_validator


class SaveEventsUserIdHeaderSchema(BaseModel):
    """Схема для заголовка X-User-ID."""

    x_user_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Уникальный идентификатор пользователя (UUID4). "
        "Если не указан — создаётся временный анонимный профиль",
    )

    @field_validator("x_user_id")
    @classmethod
    def validate_x_user_id(cls, v: str) -> str:
        """Валидация X-User-ID."""
        from ....services.events.validators import EventsServiceValidators

        return EventsServiceValidators.validate_user_id_header(v)

    class Config:
        json_schema_extra = {
            "example": {
                "x_user_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
            }
        }
