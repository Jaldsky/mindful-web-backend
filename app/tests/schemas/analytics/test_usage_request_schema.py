from unittest import TestCase

from app.schemas.analytics import AnalyticsUsageRequestSchema
from app.services.analytics.usage.exceptions import (
    InvalidDateFormatException,
    InvalidPageException,
)


class TestAnalyticsUsageRequestSchema(TestCase):
    """Тесты для схемы запроса аналитики использования."""

    def setUp(self):
        """Настройка базовых данных для тестов."""
        self.valid_payload = {
            "from_date": "05-04-2025",
            "to_date": "10-04-2025",
            "page": 1,
        }

    def test_valid_request_passes(self):
        """Корректные данные успешно валидируются."""
        schema = AnalyticsUsageRequestSchema(**self.valid_payload)

        self.assertEqual(schema.from_date, "05-04-2025")
        self.assertEqual(schema.to_date, "10-04-2025")
        self.assertEqual(schema.page, 1)

    def test_default_page_value(self):
        """Если page не указан, используется значение по умолчанию."""
        payload = {
            "from_date": "05-04-2025",
            "to_date": "10-04-2025",
        }

        schema = AnalyticsUsageRequestSchema(**payload)

        self.assertEqual(schema.page, 1)

    def test_date_strings_are_trimmed(self):
        """Пробелы в начале и конце строк дат удаляются."""
        payload = {
            "from_date": "  05-04-2025  ",
            "to_date": "  10-04-2025  ",
            "page": 1,
        }

        schema = AnalyticsUsageRequestSchema(**payload)

        self.assertEqual(schema.from_date, "05-04-2025")
        self.assertEqual(schema.to_date, "10-04-2025")

    def test_invalid_date_format_missing_parts(self):
        """Неверный формат даты - недостаточно частей."""
        invalid_formats = [
            "05-04",
            "05",
            "05-04-2025-01",
            "",
        ]

        for invalid_format in invalid_formats:
            with self.subTest(invalid_format=invalid_format):
                payload = {
                    "from_date": invalid_format,
                    "to_date": "10-04-2025",
                    "page": 1,
                }

                with self.assertRaises(InvalidDateFormatException) as cm:
                    AnalyticsUsageRequestSchema(**payload)

                self.assertIn("Invalid date format", str(cm.exception))

    def test_invalid_date_format_non_numeric_components(self):
        """Неверный формат даты - компоненты не являются числами."""
        invalid_dates = [
            ("ab-04-2025", "Date components must be numbers"),
            ("05-cd-2025", "Date components must be numbers"),
            ("05-04-efgh", "Date components must be numbers"),
            ("05-04-20.5", "Date components must be numbers"),
        ]

        for invalid_date, expected_message in invalid_dates:
            with self.subTest(invalid_date=invalid_date):
                payload = {
                    "from_date": invalid_date,
                    "to_date": "10-04-2025",
                    "page": 1,
                }

                with self.assertRaises(InvalidDateFormatException) as cm:
                    AnalyticsUsageRequestSchema(**payload)

                self.assertIn(expected_message, str(cm.exception))

    def test_invalid_date_format_wrong_separator(self):
        """Неверный формат даты - неправильный разделитель."""
        invalid_dates = [
            "05.04-2025",
            "05/04/2025",
            "05 04 2025",
        ]

        for invalid_date in invalid_dates:
            with self.subTest(invalid_date=invalid_date):
                payload = {
                    "from_date": invalid_date,
                    "to_date": "10-04-2025",
                    "page": 1,
                }

                with self.assertRaises(InvalidDateFormatException) as cm:
                    AnalyticsUsageRequestSchema(**payload)

                self.assertIn("Invalid date format", str(cm.exception))

    def test_invalid_page_less_than_one(self):
        """Номер страницы меньше 1 вызывает исключение."""
        payload = {
            "from_date": "05-04-2025",
            "to_date": "10-04-2025",
            "page": 0,
        }

        with self.assertRaises(InvalidPageException) as cm:
            AnalyticsUsageRequestSchema(**payload)

        self.assertIn("Page must be greater than or equal to 1", str(cm.exception))

    def test_invalid_page_negative(self):
        """Отрицательный номер страницы вызывает исключение."""
        payload = {
            "from_date": "05-04-2025",
            "to_date": "10-04-2025",
            "page": -1,
        }

        with self.assertRaises(InvalidPageException) as cm:
            AnalyticsUsageRequestSchema(**payload)

        self.assertIn("Page must be greater than or equal to 1", str(cm.exception))

    def test_valid_page_greater_than_one(self):
        """Номер страницы больше 1 валиден."""
        payload = {
            "from_date": "05-04-2025",
            "to_date": "10-04-2025",
            "page": 5,
        }

        schema = AnalyticsUsageRequestSchema(**payload)

        self.assertEqual(schema.page, 5)

    def test_both_dates_invalid_format(self):
        """Обе даты с неверным форматом."""
        payload = {
            "from_date": "invalid",
            "to_date": "also-invalid",
            "page": 1,
        }

        with self.assertRaises(InvalidDateFormatException):
            AnalyticsUsageRequestSchema(**payload)

    def test_same_from_and_to_date(self):
        """Одинаковые даты начала и конца валидны."""
        payload = {
            "from_date": "05-04-2025",
            "to_date": "05-04-2025",
            "page": 1,
        }

        schema = AnalyticsUsageRequestSchema(**payload)

        self.assertEqual(schema.from_date, "05-04-2025")
        self.assertEqual(schema.to_date, "05-04-2025")
