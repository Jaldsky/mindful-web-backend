from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator

from ....config import DATE_FORMATS
from ....services.analytics.usage.exceptions import (
    InvalidDateFormatException,
    InvalidPageException,
)


class AnalyticsUsageRequestSchema(BaseModel):
    """Схема запроса для получения статистики использования доменов."""

    from_date: date = Field(..., description="Начало интервала")
    to_date: date = Field(..., description="Конец интервала")
    page: int = Field(default=1, description="Номер страницы")

    @field_validator("from_date", "to_date", mode="before")
    @classmethod
    def parse_date_string(cls, v) -> date:
        """Парсит строку даты, пробуя разные форматы.

        Args:
            v: Значение для парсинга (строка или date).

        Returns:
            Объект date.

        Raises:
            InvalidDateFormatException: Если ни один формат не подошел.
        """
        if isinstance(v, date):
            return v

        v = v.strip()
        for date_format in DATE_FORMATS:
            try:
                return datetime.strptime(v, date_format).date()
            except ValueError:
                continue
        raise InvalidDateFormatException("Invalid date format")

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
