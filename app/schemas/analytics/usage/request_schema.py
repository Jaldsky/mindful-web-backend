from datetime import date
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class AnalyticsUsageRequestSchema(BaseModel):
    """Схема запроса для получения статистики использования доменов."""

    from_date: date = Field(..., description="Начало интервала")
    to_date: date = Field(..., description="Конец интервала")
    page: int = Field(default=1, description="Номер страницы")

    @field_validator("from_date", "to_date", mode="before")
    @classmethod
    def normalize_date(cls, v: Any) -> Any:
        """Нормализация даты."""
        if not isinstance(v, str):
            return v
        from ....services.analytics.normalizers import AnalyticsServiceNormalizers

        return AnalyticsServiceNormalizers.normalize_date(v)

    @field_validator("from_date", "to_date", mode="before")
    @classmethod
    def validate_date(cls, v: Any) -> date:
        """Валидация даты (422)."""
        from ....services.analytics.validators import AnalyticsServiceValidators

        return AnalyticsServiceValidators.validate_date(v)

    @model_validator(mode="after")
    def validate_time_range(self) -> "AnalyticsUsageRequestSchema":
        """Валидация временного диапазона (422)."""
        from ....services.analytics.validators import AnalyticsServiceValidators

        AnalyticsServiceValidators.validate_time_range(self.from_date, self.to_date)
        return self

    @field_validator("page")
    @classmethod
    def validate_page(cls, v: int) -> int:
        """Валидация номера страницы."""
        from ....services.analytics.validators import AnalyticsServiceValidators

        AnalyticsServiceValidators.validate_page(v)
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "from": "05-04-2025",
                "to": "05-04-2025",
                "page": 1,
            }
        }
