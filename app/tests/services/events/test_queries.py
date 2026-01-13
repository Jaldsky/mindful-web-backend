import asyncio
from unittest import TestCase
from unittest.mock import AsyncMock
from uuid import uuid4

from sqlalchemy.dialects import postgresql

from app.services.events.queries import bulk_insert_attention_events, insert_user_if_not_exists


class TestEventsQueries(TestCase):
    """Тесты функций queries.py (работа с БД на уровне выражений)."""

    def setUp(self):
        self.session = AsyncMock()

    def _run_async(self, coro):
        return asyncio.run(coro)

    def test_insert_user_if_not_exists_compiles_on_conflict(self):
        user_id = uuid4()

        self._run_async(insert_user_if_not_exists(self.session, user_id))

        self.session.execute.assert_awaited_once()
        stmt = self.session.execute.call_args[0][0]
        sql = str(stmt.compile(dialect=postgresql.dialect()))

        self.assertIn("INSERT INTO users", sql)
        self.assertIn("ON CONFLICT (id) DO NOTHING", sql)

    def test_bulk_insert_attention_events_calls_execute(self):
        values = [
            {"user_id": uuid4(), "domain": "example.com", "event_type": "active", "timestamp": "2025-01-01T00:00:00Z"}
        ]

        self._run_async(bulk_insert_attention_events(self.session, values))

        self.session.execute.assert_awaited_once()
        args, _ = self.session.execute.call_args
        self.assertEqual(args[1], values)
