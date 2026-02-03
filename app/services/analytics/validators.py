from datetime import date, datetime
from typing import NoReturn

from .constants import MIN_PAGE
from .exceptions import (
    InvalidDateFormatException,
    InvalidPageException,
    InvalidTimeRangeException,
)
from .types import Date, DateStr, Page
from ...config import DATE_FORMATS


class AnalyticsServiceValidators:
    """Валидаторы для analytics-сервиса."""

    @classmethod
    def validate_date(cls, date_: Date | DateStr) -> Date | NoReturn:
        """Метод бизнес-валидации и парсинга даты.

        Args:
            date_: Дата (date) или строка даты.

        Returns:
            Объект date.

        Raises:
            InvalidDateFormatException: Если формат даты не распознан.
        """
        if isinstance(date_, date):
            return date_
        if not isinstance(date_, str):
            raise InvalidDateFormatException("analytics.errors.invalid_date_format")

        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(date_, fmt).date()
            except ValueError:
                continue

        raise InvalidDateFormatException("analytics.errors.invalid_date_format")

    @classmethod
    def validate_time_range(cls, from_date: Date, to_date: Date) -> None | NoReturn:
        """Метод валидации временного диапазона.

        Args:
            from_date: Дата начала диапозона.
            to_date: Дата конца диапозона.

        Raises:
            InvalidTimeRangeException: Диапазон не корректен.
        """
        if to_date < from_date:
            raise InvalidTimeRangeException("analytics.errors.invalid_time_range")

    @classmethod
    def validate_page(cls, page: Page) -> None | NoReturn:
        """Метод валидации номера страницы.

        Args:
            page: Номер страницы.

        Raises:
            InvalidPageException: Номер страницы не корректен.
        """

        if not isinstance(page, int):
            raise InvalidPageException("analytics.errors.invalid_page_type")

        if page < MIN_PAGE:
            raise InvalidPageException("analytics.errors.invalid_page")
