import asyncio
import unittest
from unittest import TestCase
from unittest.mock import AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.healthcheck import DatabaseHealthcheckService
from app.services.healthcheck.exceptions import HealthcheckServiceUnavailableException


class TestDatabaseHealthcheckService(TestCase):
    """Тесты для DatabaseHealthcheckService."""

    def setUp(self):
        """Настройка тестового окружения."""
        self.session = AsyncMock(spec=AsyncSession)

    def _run_async(self, coro):
        """Вспомогательный метод для запуска async функций."""
        return asyncio.run(coro)

    def test_database_healthcheck_service_initialization(self):
        """Тест инициализации DatabaseHealthcheckService."""
        service = DatabaseHealthcheckService(session=self.session)
        self.assertIsNotNone(service)
        self.assertIsNotNone(service.session)

    @patch("app.services.healthcheck.use_cases.database_healthcheck.check_database_connection")
    def test_database_healthcheck_exec_success(self, mock_check):
        """Тест успешного выполнения database healthcheck."""
        # Настраиваем мок для возврата True
        mock_check.return_value = True

        service = DatabaseHealthcheckService(session=self.session)
        result = self._run_async(service.exec())

        self.assertIsNone(result)
        mock_check.assert_called_once_with(self.session)

    @patch("app.services.healthcheck.use_cases.database_healthcheck.check_database_connection")
    def test_database_healthcheck_exec_database_unavailable(self, mock_check):
        """Тест database healthcheck при недоступной БД."""
        # Настраиваем мок для возврата False
        mock_check.return_value = False

        service = DatabaseHealthcheckService(session=self.session)

        with self.assertRaises(HealthcheckServiceUnavailableException):
            self._run_async(service.exec())

        mock_check.assert_called_once_with(self.session)


if __name__ == "__main__":
    unittest.main()
