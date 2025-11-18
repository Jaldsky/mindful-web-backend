import asyncio
from unittest import TestCase
from unittest.mock import AsyncMock, patch, Mock
from uuid import UUID, uuid4
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import text

from app.db.models.base import Base
from app.db.session.manager import ManagerAsync
from app.services.events.send_events import SendEventsService
from app.schemas.events.send_events_request_schema import SendEventsRequestSchema, SendEventData
from app.services.events.exceptions import EventsServiceException, EventsServiceMessages


class TestEventsService(TestCase):
    """Тесты для EventsService."""

    def setUp(self):
        self.logger = Mock()
        self.database_url = "sqlite+aiosqlite:///:memory:"
        self.session = AsyncMock()
        self.session.add = Mock()
        self.user_id: UUID = uuid4()
        self.valid_event_data = SendEventData(event="active", domain="example.com", timestamp="2025-04-05T10:00:00Z")
        self.valid_data = [self.valid_event_data]

    def _run_async(self, coro):
        """Вспомогательный метод для запуска асинхронного кода."""
        return asyncio.run(coro)

    @patch("app.services.events.send_events.logger")
    def test_exec_success(self, mock_logger):
        """Успешная обработка событий на моках."""
        self._run_async(SendEventsService(self.session).exec(self.valid_data, self.user_id))

        self.session.execute.assert_called()
        self.session.add.assert_called_once()
        self.session.commit.assert_awaited_once()
        mock_logger.info.assert_called_with(
            f"Successfully processed {len(self.valid_data)} events for user {self.user_id}"
        )

    @patch("app.services.events.send_events.logger")
    def test_exec_user_creation_fails(self, mock_logger):
        """Ошибка при создании/получении пользователя."""
        self.session.execute.side_effect = Exception("DB down")

        with self.assertRaises(EventsServiceException) as cm:
            self._run_async(SendEventsService(self.session).exec(self.valid_data, self.user_id))

        self.session.rollback.assert_awaited_once()
        mock_logger.error.assert_called()
        self.assertEqual(
            EventsServiceMessages.GET_OR_CREATE_USER_ERROR.format(user_id=str(self.user_id)), cm.exception.message
        )

    @patch("app.services.events.send_events.logger")
    def test_exec_events_insert_fails(self, _):
        """Ошибка при подготовке/добавлении событий."""
        with patch.object(
            SendEventsService,
            "_insert_events",
            side_effect=EventsServiceException(EventsServiceMessages.ADD_EVENTS_ERROR),
        ):
            with self.assertRaises(EventsServiceException) as cm:
                self._run_async(SendEventsService(self.session).exec(self.valid_data, self.user_id))

            self.session.rollback.assert_awaited_once()
            self.assertEqual(EventsServiceMessages.ADD_EVENTS_ERROR, cm.exception.message)

    @patch("app.services.events.send_events.logger")
    def test_exec_integrity_error(self, mock_logger):
        """Обработка IntegrityError."""
        self.session.commit.side_effect = IntegrityError(
            statement="INSERT INTO ...", params={}, orig=Exception("foreign key violation")
        )
        with self.assertRaises(EventsServiceException) as cm:
            self._run_async(SendEventsService(self.session).exec(self.valid_data, self.user_id))

        self.session.rollback.assert_awaited_once()
        mock_logger.error.assert_called()
        self.assertEqual(EventsServiceMessages.DATA_INTEGRITY_ERROR, cm.exception.message)

    @patch("app.services.events.send_events.logger")
    def test_exec_sqlalchemy_error(self, mock_logger):
        """Обработка общей ошибки SQLAlchemy."""
        self.session.commit.side_effect = SQLAlchemyError("Connection lost")

        with self.assertRaises(EventsServiceException) as cm:
            self._run_async(SendEventsService(self.session).exec(self.valid_data, self.user_id))

        self.session.rollback.assert_awaited_once()
        mock_logger.error.assert_called()
        self.assertEqual(EventsServiceMessages.DATA_SAVE_ERROR, cm.exception.message)

    @patch("app.services.events.send_events.logger")
    def test_exec_unexpected_error22(self, mock_logger):
        """Обработка неожиданного исключения (не SQLAlchemy)."""
        self.session.commit.side_effect = ValueError("Something weird")

        with self.assertRaises(EventsServiceException) as cm:
            self._run_async(SendEventsService(self.session).exec(self.valid_data, self.user_id))

        self.session.rollback.assert_awaited_once()
        mock_logger.error.assert_called()
        self.assertEqual(EventsServiceMessages.UNEXPECTED_ERROR, cm.exception.message)

    @patch("app.services.events.send_events.logger")
    def test_ensure_user_exists_success(self, _):
        """Метод _ensure_user_exists работает без ошибок."""
        self._run_async(SendEventsService(self.session)._ensure_user_exists(self.user_id))

        call_args = self.session.execute.call_args
        self.assertIsNotNone(call_args)
        insert_stmt = call_args[0][0]

        compiled = insert_stmt.compile(dialect=postgresql.dialect())
        sql_text = str(compiled)

        self.assertEqual("INSERT INTO users (id) VALUES (%(id)s::UUID) ON CONFLICT (id) DO NOTHING", sql_text)

    @patch("app.services.events.send_events.logger")
    def test_insert_events_success(self, mock_logger):
        """Метод _insert_events корректно создаёт объекты AttentionEvent."""
        self._run_async(SendEventsService(self.session)._insert_events([self.valid_event_data], self.user_id))

        self.session.add.assert_called_once()
        added_event = self.session.add.call_args[0][0]
        self.assertEqual(added_event.user_id, self.user_id)
        self.assertEqual(added_event.domain, "example.com")
        self.assertEqual(added_event.event_type, "active")

    def test_events_service_real_db_flow(self):
        """Полный цикл: создание пользователя, сохранение событий, проверка в БД."""
        manager = ManagerAsync(logger=self.logger, database_url=self.database_url)

        async def _test_session():
            engine = manager.get_engine()
            async with engine.begin() as session:
                await session.run_sync(Base.metadata.create_all)

            user_id = str(uuid4())

            event_data = SendEventData(event="active", domain="example.com", timestamp="2025-04-05T10:00:00Z")
            payload = SendEventsRequestSchema(data=[event_data])

            async with manager.get_session() as session:
                service = SendEventsService(session)
                await service.exec(payload.data, UUID(user_id))

            async with manager.get_session() as session:
                result = await session.execute(text("SELECT * FROM users"))
                user_row = result.fetchone()
                self.assertIsNotNone(user_row)

                result = await session.execute(text("SELECT * FROM attention_events"))
                event_row = result.fetchone()
                self.assertIsNotNone(event_row)
                self.assertEqual(event_row[2], "example.com")
                self.assertEqual(event_row[3], "active")

        self._run_async(_test_session())
        self.logger.error.assert_not_called()
