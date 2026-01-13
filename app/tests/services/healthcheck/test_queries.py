import asyncio
import unittest
from unittest import TestCase
from unittest.mock import AsyncMock, Mock

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.healthcheck.queries import check_database_connection


class TestHealthcheckQueries(TestCase):
    """Тесты для healthcheck queries."""

    def setUp(self):
        """Настройка тестового окружения."""
        self.session = AsyncMock(spec=AsyncSession)

    def _run_async(self, coro):
        """Вспомогательный метод для запуска async функций."""
        return asyncio.run(coro)

    def test_check_database_connection_success(self):
        """Тест успешной проверки подключения к БД."""
        mock_result = Mock()
        mock_result.scalar.return_value = 1
        self.session.execute = AsyncMock(return_value=mock_result)

        is_available = self._run_async(check_database_connection(self.session))

        self.assertTrue(is_available)
        self.session.execute.assert_called_once()

    def test_check_database_connection_wrong_result(self):
        """Тест проверки подключения к БД при неверном результате."""
        mock_result = Mock()
        mock_result.scalar.return_value = 0
        self.session.execute = AsyncMock(return_value=mock_result)

        is_available = self._run_async(check_database_connection(self.session))

        self.assertFalse(is_available)
        self.session.execute.assert_called_once()

    def test_check_database_connection_none_result(self):
        """Тест проверки подключения к БД при None результате."""
        mock_result = Mock()
        mock_result.scalar.return_value = None
        self.session.execute = AsyncMock(return_value=mock_result)

        is_available = self._run_async(check_database_connection(self.session))

        self.assertFalse(is_available)
        self.session.execute.assert_called_once()

    def test_check_database_connection_exception(self):
        """Тест проверки подключения к БД при исключении."""
        self.session.execute = AsyncMock(side_effect=Exception("Connection failed"))

        is_available = self._run_async(check_database_connection(self.session))

        self.assertFalse(is_available)
        self.session.execute.assert_called_once()


if __name__ == "__main__":
    unittest.main()
