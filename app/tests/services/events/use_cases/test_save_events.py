import asyncio
from unittest import TestCase
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.schemas.events.save.request_schema import SaveEventData
from app.services.events.exceptions import (
    DataIntegrityViolationException,
    TransactionFailedException,
    UnexpectedEventsException,
)
from app.services.events.use_cases.save_events import SaveEventsService


class TestSaveEventsService(TestCase):
    """Тесты use-case SaveEventsService (unit)."""

    def setUp(self):
        self.session = AsyncMock()

        tx = AsyncMock()
        tx.__aenter__.return_value = None
        tx.__aexit__.return_value = None
        self.session.begin.return_value = tx

        self.user_id = uuid4()
        self.data = [
            SaveEventData(event="active", domain="example.com", timestamp="2025-04-05T10:00:00Z"),
            SaveEventData(event="inactive", domain="example.com", timestamp="2025-04-05T10:01:00Z"),
        ]

    def _run_async(self, coro):
        return asyncio.run(coro)

    @patch("app.services.events.use_cases.save_events.bulk_insert_attention_events", new_callable=AsyncMock)
    @patch("app.services.events.use_cases.save_events.insert_user_if_not_exists", new_callable=AsyncMock)
    def test_exec_success(self, mock_insert_user, mock_bulk_insert):
        service = SaveEventsService(session=self.session, data=self.data, user_id=self.user_id)

        self._run_async(service.exec())

        self.session.begin.assert_called_once()
        mock_insert_user.assert_awaited_once_with(self.session, self.user_id)

        self.assertTrue(mock_bulk_insert.await_count == 1)
        _, values = mock_bulk_insert.await_args.args
        self.assertEqual(len(values), 2)
        self.assertEqual(values[0]["user_id"], self.user_id)
        self.assertEqual(values[0]["domain"], "example.com")
        self.assertEqual(values[0]["event_type"], "active")

    @patch("app.services.events.use_cases.save_events.bulk_insert_attention_events", new_callable=AsyncMock)
    @patch("app.services.events.use_cases.save_events.insert_user_if_not_exists", new_callable=AsyncMock)
    def test_exec_integrity_error_maps_exception(self, mock_insert_user, mock_bulk_insert):
        mock_bulk_insert.side_effect = IntegrityError("INSERT", params={}, orig=Exception("fk"))

        service = SaveEventsService(session=self.session, data=self.data, user_id=self.user_id)

        with self.assertRaises(DataIntegrityViolationException):
            self._run_async(service.exec())

    @patch("app.services.events.use_cases.save_events.bulk_insert_attention_events", new_callable=AsyncMock)
    @patch("app.services.events.use_cases.save_events.insert_user_if_not_exists", new_callable=AsyncMock)
    def test_exec_sqlalchemy_error_maps_exception(self, mock_insert_user, mock_bulk_insert):
        mock_bulk_insert.side_effect = SQLAlchemyError("db down")

        service = SaveEventsService(session=self.session, data=self.data, user_id=self.user_id)

        with self.assertRaises(TransactionFailedException):
            self._run_async(service.exec())

    @patch("app.services.events.use_cases.save_events.bulk_insert_attention_events", new_callable=AsyncMock)
    @patch("app.services.events.use_cases.save_events.insert_user_if_not_exists", new_callable=AsyncMock)
    def test_exec_unexpected_error_maps_exception(self, mock_insert_user, mock_bulk_insert):
        mock_bulk_insert.side_effect = ValueError("boom")

        service = SaveEventsService(session=self.session, data=self.data, user_id=self.user_id)

        with self.assertRaises(UnexpectedEventsException):
            self._run_async(service.exec())
