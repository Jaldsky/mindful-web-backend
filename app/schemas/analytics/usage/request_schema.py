from pydantic import BaseModel, Field, field_validator

from ....services.analytics.usage.exceptions import (
    InvalidDateFormatException,
    InvalidPageException,
)


class AnalyticsUsageRequestSchema(BaseModel):
    """Схема запроса для получения статистики использования доменов."""

    from_date: str = Field(..., description="Начало интервала")
    to_date: str = Field(..., description="Конец интервала")
    page: int = Field(default=1, description="Номер страницы")

    @field_validator("from_date", "to_date")
    @classmethod
    def validate_date_string(cls, v) -> str:
        """Валидирует строку даты в формате DD-MM-YYYY."""
        v = v.strip()
        parts = v.split("-")
        if len(parts) != 3:
            raise InvalidDateFormatException("Invalid date format")
        for part in parts:
            if not part.isdigit():
                raise InvalidDateFormatException("Date components must be numbers")
        return v

    @field_validator("page")
    @classmethod
    def validate_page(cls, v: int) -> int:
        """Валидация номера страницы."""
        if v < 1:
            raise InvalidPageException("Page must be greater than or equal to 1")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "from": "05-04-2025",
                "to": "05-04-2025",
                "page": 1,
            }
        }
