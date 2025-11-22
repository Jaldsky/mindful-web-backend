import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from unittest import TestCase
from unittest.mock import AsyncMock, patch, Mock, MagicMock
from uuid import UUID, uuid4
from datetime import date, datetime, time, timezone
from sqlalchemy.exc import SQLAlchemyError

from app.services.analytics.usage.main import AnalyticsUsageService
from app.services.analytics.usage.exceptions import (
    DatabaseQueryFailedException,
    UnexpectedUsageException,
    UsageServiceMessages,
)
from app.schemas.analytics.usage.response_ok_schema import AnalyticsUsageResponseOkSchema


class TestUsageService(TestCase):
    """Тесты для AnalyticsUsageService."""

    def setUp(self):
        self.logger = Mock()
        self.database_url = "sqlite+aiosqlite:///:memory:"
        self.session = AsyncMock()
        self.user_id: UUID = uuid4()
        self.start_date = date(2025, 4, 5)
        self.end_date = date(2025, 4, 6)
        self.page = 1
        self.page_size = 20

    def _run_async(self, coro):
        """Вспомогательный метод для запуска асинхронного кода."""
        return asyncio.run(coro)

    @patch("app.services.analytics.usage.main.logger")
    @patch("app.services.analytics.usage.main.AnalyticsUsageService._load_sql")
    @patch("app.services.analytics.usage.main.isinstance")
    def test_exec_success(self, mock_isinstance, mock_load_sql, mock_logger):
        """Успешное выполнение запроса аналитики на моках."""
        mock_isinstance.side_effect = lambda obj, cls: cls == AsyncSession
        mock_load_sql.return_value = "SELECT domain, category, total_seconds, total_items FROM ranked"
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = [
            {"domain": "example.com", "category": "work", "total_seconds": 3600, "total_items": 1}
        ]
        self.session.execute = AsyncMock(return_value=mock_result)

        result = self._run_async(
            AnalyticsUsageService(self.session, self.user_id).exec(
                self.start_date, self.end_date, self.page, self.page_size
            )
        )

        self.assertIsInstance(result, AnalyticsUsageResponseOkSchema)
        self.assertEqual(result.code, "OK")
        self.assertEqual(result.from_date, self.start_date)
        self.assertEqual(result.to_date, self.end_date)
        self.assertEqual(result.pagination.page, self.page)
        self.assertEqual(result.pagination.per_page, self.page_size)
        self.assertEqual(len(result.data), 1)
        self.assertEqual(result.data[0].domain, "example.com")
        mock_logger.info.assert_called_with(
            f"Successfully computed usage analytics (async, 1 SQL) for user {self.user_id}"
        )

    @patch("app.services.analytics.usage.main.logger")
    @patch("app.services.analytics.usage.main.AnalyticsUsageService._load_sql")
    @patch("app.services.analytics.usage.main.isinstance")
    def test_exec_database_query_fails(self, mock_isinstance, mock_load_sql, mock_logger):
        """Ошибка при запросе к базе данных."""
        mock_isinstance.side_effect = lambda obj, cls: cls == AsyncSession
        mock_load_sql.return_value = "SELECT * FROM test"
        self.session.execute = AsyncMock(side_effect=SQLAlchemyError("Connection lost"))

        with self.assertRaises(DatabaseQueryFailedException) as cm:
            self._run_async(
                AnalyticsUsageService(self.session, self.user_id).exec(
                    self.start_date, self.end_date, self.page, self.page_size
                )
            )

        mock_logger.error.assert_called()
        self.assertEqual(UsageServiceMessages.DATABASE_QUERY_ERROR, cm.exception.message)

    @patch("app.services.analytics.usage.main.logger")
    @patch("app.services.analytics.usage.main.AnalyticsUsageService._load_sql")
    @patch("app.services.analytics.usage.main.isinstance")
    def test_exec_unexpected_error(self, mock_isinstance, mock_load_sql, mock_logger):
        """Обработка неожиданного исключения."""
        mock_isinstance.side_effect = lambda obj, cls: cls == AsyncSession
        mock_load_sql.return_value = "SELECT * FROM test"
        self.session.execute = AsyncMock(side_effect=ValueError("Something weird"))

        with self.assertRaises(UnexpectedUsageException) as cm:
            self._run_async(
                AnalyticsUsageService(self.session, self.user_id).exec(
                    self.start_date, self.end_date, self.page, self.page_size
                )
            )

        mock_logger.error.assert_called()
        self.assertEqual(UsageServiceMessages.UNEXPECTED_ERROR, cm.exception.message)

    @patch("app.services.analytics.usage.main.logger")
    def test_normalize_pagination(self, _):
        """Метод _normalize_pagination корректно нормализует параметры."""
        service = AnalyticsUsageService(self.session, self.user_id)

        test_cases = [
            (2, 10, 2, 10),
            (-1, -5, 1, 20),
            (0, 0, 1, 20),
        ]

        for input_page, input_page_size, expected_page, expected_page_size in test_cases:
            with self.subTest(page=input_page, page_size=input_page_size):
                page, page_size = service._normalize_pagination(input_page, input_page_size)
                self.assertEqual(page, expected_page)
                self.assertEqual(page_size, expected_page_size)

    @patch("app.services.analytics.usage.main.logger")
    def test_build_time_range(self, _):
        """Метод _build_time_range корректно строит временной диапазон."""
        service = AnalyticsUsageService(self.session, self.user_id)

        start_date = date(2025, 4, 5)
        end_date = date(2025, 4, 6)

        start_dt, end_dt = service._build_time_range(start_date, end_date)

        self.assertIsInstance(start_dt, datetime)
        self.assertIsInstance(end_dt, datetime)
        self.assertEqual(start_dt.date(), start_date)
        self.assertEqual(end_dt.date(), end_date)
        self.assertEqual(start_dt.time(), time.min)
        self.assertEqual(end_dt.time(), time.max)
        self.assertEqual(start_dt.tzinfo, timezone.utc)
        self.assertEqual(end_dt.tzinfo, timezone.utc)

    @patch("app.services.analytics.usage.main.logger")
    @patch("app.services.analytics.usage.main.read_text_file")
    def test_load_sql(self, mock_read_file, _):
        """Метод _load_sql корректно загружает SQL из файла."""
        mock_read_file.return_value = "SELECT * FROM test"
        service = AnalyticsUsageService(self.session, self.user_id)

        sql_text = service._load_sql()

        self.assertEqual(sql_text, "SELECT * FROM test")
        mock_read_file.assert_called_once()

    @patch("app.services.analytics.usage.main.logger")
    @patch("app.services.analytics.usage.main.isinstance")
    def test_execute_query_async_session(self, mock_isinstance, _):
        """Метод _execute_query работает с AsyncSession."""
        mock_isinstance.side_effect = lambda obj, cls: cls == AsyncSession
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = [{"test": "value"}]
        self.session.execute = AsyncMock(return_value=mock_result)

        service = AnalyticsUsageService(self.session, self.user_id)
        result = self._run_async(service._execute_query("SELECT * FROM test", {"param": "value"}))

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["test"], "value")
        self.session.execute.assert_awaited_once()

    @patch("app.services.analytics.usage.main.logger")
    @patch("app.services.analytics.usage.main.AnalyticsUsageService._load_sql")
    @patch("app.services.analytics.usage.main.isinstance")
    def test_exec_empty_result(self, mock_isinstance, mock_load_sql, mock_logger):
        """Обработка пустого результата запроса."""
        mock_isinstance.side_effect = lambda obj, cls: cls == AsyncSession
        mock_load_sql.return_value = "SELECT domain, category, total_seconds, total_items FROM ranked"
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        self.session.execute = AsyncMock(return_value=mock_result)

        result = self._run_async(
            AnalyticsUsageService(self.session, self.user_id).exec(
                self.start_date, self.end_date, self.page, self.page_size
            )
        )

        self.assertIsInstance(result, AnalyticsUsageResponseOkSchema)
        self.assertEqual(result.pagination.total_items, 0)
        self.assertEqual(len(result.data), 0)

    @patch("app.services.analytics.usage.main.logger")
    @patch("app.services.analytics.usage.main.AnalyticsUsageService._load_sql")
    @patch("app.services.analytics.usage.main.isinstance")
    def test_exec_pagination_calculation(self, mock_isinstance, mock_load_sql, mock_logger):
        """Корректный расчет пагинации."""
        mock_isinstance.side_effect = lambda obj, cls: cls == AsyncSession
        mock_load_sql.return_value = "SELECT domain, category, total_seconds, total_items FROM ranked"
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = [
            {"domain": "example.com", "category": "work", "total_seconds": 3600, "total_items": 25}
        ]
        self.session.execute = AsyncMock(return_value=mock_result)

        result = self._run_async(
            AnalyticsUsageService(self.session, self.user_id).exec(
                self.start_date, self.end_date, page=1, page_size=10
            )
        )

        self.assertEqual(result.pagination.total_items, 25)
        self.assertEqual(result.pagination.total_pages, 3)
        self.assertEqual(result.pagination.page, 1)
        self.assertEqual(result.pagination.per_page, 10)
