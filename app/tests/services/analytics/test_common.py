from unittest import TestCase
from unittest.mock import patch

from app.services.analytics.common import load_compute_domain_usage_sql


class TestAnalyticsCommon(TestCase):
    """Тесты для app.services.analytics.common."""

    @patch("app.services.analytics.common.read_text_file")
    def test_load_compute_domain_usage_sql_reads_file(self, mock_read_text_file):
        """SQL loader читает файл и возвращает его содержимое."""
        mock_read_text_file.return_value = "SELECT 1"

        sql = load_compute_domain_usage_sql()

        self.assertEqual(sql, "SELECT 1")
        mock_read_text_file.assert_called_once()
