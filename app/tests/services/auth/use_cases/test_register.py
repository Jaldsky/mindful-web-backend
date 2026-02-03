import asyncio
import unittest
from unittest import TestCase
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.base import Base
from app.db.models.tables import User, VerificationCode
from app.db.session.manager import ManagerAsync
from app.services.auth import RegisterService
from app.services.auth.exceptions import (
    EmailAlreadyExistsException,
    EmailSendFailedException,
    InvalidEmailFormatException,
    InvalidPasswordFormatException,
    InvalidUsernameFormatException,
    UsernameAlreadyExistsException,
)
from app.schemas.auth import RegisterRequestSchema


class TestRegisterServiceMethods(TestCase):
    """Тесты для отдельных методов RegisterService."""

    def setUp(self):
        self.session = AsyncMock(spec=AsyncSession)

    def _run_async(self, coro):
        return asyncio.run(coro)

    def test_create_user(self):
        """Тест создания пользователя."""
        added_objects: list[object] = []

        def mock_add(obj):
            added_objects.append(obj)

        self.session.add = Mock(side_effect=mock_add)
        self.session.flush = AsyncMock()

        service = RegisterService()
        user = self._run_async(service._create_user(self.session, "testuser", "test@example.com", "password123"))

        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertFalse(user.is_verified)
        self.assertIsNotNone(user.password)
        self.session.add.assert_called_once()
        self.session.flush.assert_not_awaited()

    def test_create_verification_code(self):
        """Тест создания кода подтверждения."""
        user_id = uuid4()
        added_objects: list[object] = []

        def mock_add(obj):
            added_objects.append(obj)

        self.session.add = Mock(side_effect=mock_add)

        service = RegisterService()
        code = self._run_async(service._create_verification_code(self.session, user_id))

        self.assertIsInstance(code, str)
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())
        self.session.add.assert_called_once()
        self.assertEqual(len(added_objects), 1)

    def test_check_uniqueness_no_conflicts(self):
        """Тест проверки уникальности без конфликтов."""
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        self.session.execute = AsyncMock(return_value=mock_result)

        service = RegisterService()
        self._run_async(service._check_uniqueness(self.session, "testuser", "test@example.com"))
        self.session.execute.assert_called_once()

    def test_check_uniqueness_username_exists(self):
        """Тест проверки уникальности при существующем username."""
        existing_user = Mock()
        existing_user.username = "testuser"
        existing_user.email = "other@example.com"

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [existing_user]
        self.session.execute = AsyncMock(return_value=mock_result)

        service = RegisterService()
        with self.assertRaises(UsernameAlreadyExistsException):
            self._run_async(service._check_uniqueness(self.session, "testuser", "test@example.com"))

    def test_check_uniqueness_email_exists(self):
        """Тест проверки уникальности при существующем email."""
        existing_user = Mock()
        existing_user.username = "otheruser"
        existing_user.email = "test@example.com"

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [existing_user]
        self.session.execute = AsyncMock(return_value=mock_result)

        service = RegisterService()
        with self.assertRaises(EmailAlreadyExistsException):
            self._run_async(service._check_uniqueness(self.session, "testuser", "test@example.com"))

    def test_send_verification_email_failure(self):
        """Тест ошибки отправки email."""
        from app.services.email import EmailService

        service = RegisterService()
        with unittest.mock.patch.object(EmailService, "send_verification_code", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = Exception("SMTP error")
            with self.assertRaises(EmailSendFailedException):
                self._run_async(service._send_verification_email("test@example.com", "123456"))

    def test_send_verification_email_success(self):
        """Тест успешной отправки email."""
        from app.services.email import EmailService

        service = RegisterService()
        with unittest.mock.patch.object(EmailService, "send_verification_code", new_callable=AsyncMock) as mock_send:
            self._run_async(service._send_verification_email("test@example.com", "123456"))
            mock_send.assert_awaited_once_with(to_email="test@example.com", code="123456")


class TestRegisterServiceExecUnit(TestCase):
    """Тесты для отдельных exec RegisterService."""

    def setUp(self):
        self.session = AsyncMock(spec=AsyncSession)

    def _run_async(self, coro):
        return asyncio.run(coro)

    def test_exec_calls_flush_before_create_verification_code(self):
        service = RegisterService()
        service._check_uniqueness = AsyncMock()
        user = Mock()
        user.id = uuid4()
        service._create_user = AsyncMock(return_value=user)
        call_order = []
        self.session.flush = AsyncMock(side_effect=lambda: call_order.append("flush"))
        service._create_verification_code = AsyncMock(
            side_effect=lambda session, user_id: call_order.append("code") or "123456"
        )
        service._send_verification_email = AsyncMock()
        self.session.commit = AsyncMock()
        self.session.rollback = AsyncMock()

        self._run_async(
            service.exec(
                session=self.session,
                username="testuser",
                email="test@example.com",
                password="password123",
            )
        )

        self.assertEqual(call_order, ["flush", "code"])


class TestRegisterServiceExec(TestCase):
    """Тесты для метода exec с реальной БД."""

    def setUp(self):
        self.logger = Mock()
        self.database_url = "sqlite+aiosqlite:///:memory:"

    def _run_async(self, coro):
        return asyncio.run(coro)

    def _patch_server_defaults_for_sqlite(self):
        original_user_created = User.created_at.property.columns[0].server_default
        original_user_updated = User.updated_at.property.columns[0].server_default
        original_code_created = VerificationCode.created_at.property.columns[0].server_default
        User.created_at.property.columns[0].server_default = None
        User.updated_at.property.columns[0].server_default = None
        VerificationCode.created_at.property.columns[0].server_default = None
        return original_user_created, original_user_updated, original_code_created

    def _restore_server_defaults(self, original_user_created, original_user_updated, original_code_created):
        User.created_at.property.columns[0].server_default = original_user_created
        User.updated_at.property.columns[0].server_default = original_user_updated
        VerificationCode.created_at.property.columns[0].server_default = original_code_created

    def test_exec_success(self):
        from app.services.email import EmailService

        manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                async with manager.get_session() as session:
                    service = RegisterService()
                    user = await service.exec(
                        session=session,
                        username="testuser",
                        email="test@example.com",
                        password="password123",
                    )
                    self.assertIsNotNone(user.id)

                async with manager.get_session() as session:
                    result = await session.execute(
                        text("SELECT COUNT(*) FROM users WHERE username = :username"), {"username": "testuser"}
                    )
                    self.assertEqual(result.scalar(), 1)
                    result = await session.execute(
                        text(
                            """
                            SELECT COUNT(*) FROM verification_codes vc
                            JOIN users u ON vc.user_id = u.id
                            WHERE u.username = :username
                            """
                        ),
                        {"username": "testuser"},
                    )
                    self.assertEqual(result.scalar(), 1)

            with unittest.mock.patch.object(EmailService, "send_verification_code", new_callable=AsyncMock):
                self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_username_already_exists(self):
        """Тест регистрации с существующим username."""
        from app.services.email import EmailService

        manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                async with manager.get_session() as session:
                    service1 = RegisterService()
                    await service1.exec(
                        session=session,
                        username="testuser",
                        email="test1@example.com",
                        password="password123",
                    )

                async with manager.get_session() as session:
                    service2 = RegisterService()
                    with self.assertRaises(UsernameAlreadyExistsException):
                        await service2.exec(
                            session=session,
                            username="testuser",
                            email="test2@example.com",
                            password="password123",
                        )

            with unittest.mock.patch.object(EmailService, "send_verification_code", new_callable=AsyncMock):
                self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_email_already_exists(self):
        """Тест регистрации с существующим email."""
        from app.services.email import EmailService

        manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                async with manager.get_session() as session:
                    service1 = RegisterService()
                    await service1.exec(
                        session=session,
                        username="testuser1",
                        email="test@example.com",
                        password="password123",
                    )

                async with manager.get_session() as session:
                    service2 = RegisterService()
                    with self.assertRaises(EmailAlreadyExistsException):
                        await service2.exec(
                            session=session,
                            username="testuser2",
                            email="test@example.com",
                            password="password123",
                        )

            with unittest.mock.patch.object(EmailService, "send_verification_code", new_callable=AsyncMock):
                self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_invalid_username(self):
        """Тест бизнес-валидации username на уровне request-схемы (422)."""
        ManagerAsync(logger=self.logger, database_url=self.database_url)
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                with self.assertRaises(InvalidUsernameFormatException):
                    RegisterRequestSchema(username="ab", email="test@example.com", password="password123")

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_invalid_email(self):
        """Тест бизнес-валидации email на уровне request-схемы (422)."""
        ManagerAsync(logger=self.logger, database_url=self.database_url)
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                with self.assertRaises(InvalidEmailFormatException):
                    RegisterRequestSchema(username="testuser", email="invalid-email", password="password123")

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_invalid_password(self):
        """Тест бизнес-валидации password на уровне request-схемы (422)."""
        ManagerAsync(logger=self.logger, database_url=self.database_url)
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                with self.assertRaises(InvalidPasswordFormatException):
                    RegisterRequestSchema(username="testuser", email="test@example.com", password="short")

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_email_send_failure_rolls_back(self):
        """При ошибке отправки email пользователь не должен сохраняться в БД."""
        from app.services.email import EmailService

        manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                with unittest.mock.patch.object(
                    EmailService, "send_verification_code", new_callable=AsyncMock
                ) as mock_send:
                    mock_send.side_effect = Exception("SMTP error")

                    async with manager.get_session() as session:
                        service = RegisterService()
                        with self.assertRaises(EmailSendFailedException):
                            await service.exec(
                                session=session,
                                username="testuser",
                                email="test@example.com",
                                password="password123",
                            )

                        result = await session.execute(text("SELECT COUNT(*) FROM users"))
                        self.assertEqual(result.scalar(), 0)

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)
