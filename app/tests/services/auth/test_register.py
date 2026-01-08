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
from app.services.auth.register import RegisterService, RegisterServiceBase
from app.services.auth.constants import (
    MAX_USERNAME_LENGTH,
    MAX_PASSWORD_LENGTH,
)
from app.services.auth.exceptions import (
    EmailAlreadyExistsException,
    EmailSendFailedException,
    InvalidEmailFormatException,
    InvalidPasswordFormatException,
    InvalidUsernameFormatException,
    UsernameAlreadyExistsException,
)


class TestRegisterServiceBaseNormalization(TestCase):
    """Тесты нормализации для RegisterServiceBase."""

    def setUp(self):
        """Подготовка тестовых данных."""
        self.session = AsyncMock(spec=AsyncSession)

    def test_normalize_username(self):
        """Тест нормализации username."""
        service = RegisterServiceBase(
            session=self.session, username="  TestUser  ", email="test@example.com", password="password123"
        )
        service.normalize()
        self.assertEqual(service.username, "testuser")

    def test_normalize_username_with_uppercase(self):
        """Тест нормализации username с заглавными буквами."""
        service = RegisterServiceBase(
            session=self.session, username="TESTUSER", email="test@example.com", password="password123"
        )
        service.normalize()
        self.assertEqual(service.username, "testuser")

    def test_normalize_username_with_spaces(self):
        """Тест нормализации username с пробелами."""
        service = RegisterServiceBase(
            session=self.session, username="  test  user  ", email="test@example.com", password="password123"
        )
        service.normalize()
        self.assertEqual(service.username, "test  user")

    def test_normalize_username_none(self):
        """Тест нормализации username = None."""
        service = RegisterServiceBase(
            session=self.session, username=None, email="test@example.com", password="password123"
        )
        service.normalize()
        self.assertEqual(service.username, "")

    def test_normalize_email(self):
        """Тест нормализации email."""
        service = RegisterServiceBase(
            session=self.session, username="testuser", email="  Test@Example.COM  ", password="password123"
        )
        service.normalize()
        self.assertEqual(service.email, "test@example.com")

    def test_normalize_email_with_spaces(self):
        """Тест нормализации email с пробелами."""
        service = RegisterServiceBase(
            session=self.session, username="testuser", email="  test@example.com  ", password="password123"
        )
        service.normalize()
        self.assertEqual(service.email, "test@example.com")

    def test_normalize_email_none(self):
        """Тест нормализации email = None."""
        service = RegisterServiceBase(session=self.session, username="testuser", email=None, password="password123")
        service.normalize()
        self.assertEqual(service.email, "")

    def test_normalize_password(self):
        """Тест нормализации password."""
        service = RegisterServiceBase(
            session=self.session, username="testuser", email="test@example.com", password="password123"
        )
        service.normalize()
        self.assertEqual(service.password, "password123")

    def test_normalize_password_none(self):
        """Тест нормализации password = None."""
        service = RegisterServiceBase(
            session=self.session, username="testuser", email="test@example.com", password=None
        )
        service.normalize()
        self.assertEqual(service.password, "")

    def test_normalize_all_fields(self):
        """Тест нормализации всех полей одновременно."""
        service = RegisterServiceBase(
            session=self.session, username="  TESTUSER  ", email="  Test@Example.COM  ", password="password123"
        )
        service.normalize()
        self.assertEqual(service.username, "testuser")
        self.assertEqual(service.email, "test@example.com")
        self.assertEqual(service.password, "password123")


class TestRegisterServiceBaseValidation(TestCase):
    """Тесты валидации для RegisterServiceBase."""

    def setUp(self):
        """Подготовка тестовых данных."""
        self.session = AsyncMock(spec=AsyncSession)

    def test_validate_username_too_short(self):
        """Тест валидации username слишком короткого."""
        service = RegisterServiceBase(
            session=self.session, username="ab", email="test@example.com", password="password123"
        )
        service.normalize()
        with self.assertRaises(InvalidUsernameFormatException):
            service.validate()

    def test_validate_username_too_long(self):
        """Тест валидации username слишком длинного."""
        long_username = "a" * (MAX_USERNAME_LENGTH + 1)
        service = RegisterServiceBase(
            session=self.session, username=long_username, email="test@example.com", password="password123"
        )
        service.normalize()
        with self.assertRaises(InvalidUsernameFormatException):
            service.validate()

    def test_validate_username_valid_min_length(self):
        """Тест валидации username минимальной длины."""
        service = RegisterServiceBase(
            session=self.session, username="abc", email="test@example.com", password="password123"
        )
        service.normalize()
        try:
            service.validate()
        except InvalidUsernameFormatException:
            self.fail("validate() raised InvalidUsernameFormatException unexpectedly!")

    def test_validate_username_valid_max_length(self):
        """Тест валидации username максимальной длины."""
        valid_username = "a" * MAX_USERNAME_LENGTH
        service = RegisterServiceBase(
            session=self.session, username=valid_username, email="test@example.com", password="password123"
        )
        service.normalize()
        try:
            service.validate()
        except InvalidUsernameFormatException:
            self.fail("validate() raised InvalidUsernameFormatException unexpectedly!")

    def test_validate_username_with_uppercase(self):
        """Тест валидации username с заглавными буквами."""
        service = RegisterServiceBase(
            session=self.session, username="TestUser", email="test@example.com", password="password123"
        )
        service.normalize()
        try:
            service.validate()
        except InvalidUsernameFormatException:
            self.fail("validate() raised InvalidUsernameFormatException unexpectedly!")

    def test_validate_username_with_invalid_chars(self):
        """Тест валидации username с недопустимыми символами."""
        service = RegisterServiceBase(
            session=self.session, username="test-user", email="test@example.com", password="password123"
        )
        service.normalize()
        with self.assertRaises(InvalidUsernameFormatException):
            service.validate()

    def test_validate_username_starts_with_underscore(self):
        """Тест валидации username начинающегося с underscore."""
        service = RegisterServiceBase(
            session=self.session, username="_testuser", email="test@example.com", password="password123"
        )
        service.normalize()
        with self.assertRaises(InvalidUsernameFormatException):
            service.validate()

    def test_validate_username_ends_with_underscore(self):
        """Тест валидации username заканчивающегося на underscore."""
        service = RegisterServiceBase(
            session=self.session, username="testuser_", email="test@example.com", password="password123"
        )
        service.normalize()
        with self.assertRaises(InvalidUsernameFormatException):
            service.validate()

    def test_validate_email_empty(self):
        """Тест валидации пустого email."""
        service = RegisterServiceBase(session=self.session, username="testuser", email="", password="password123")
        service.normalize()
        with self.assertRaises(InvalidEmailFormatException):
            service.validate()

    def test_validate_email_invalid_format(self):
        """Тест валидации email с неверным форматом."""
        service = RegisterServiceBase(
            session=self.session, username="testuser", email="invalid-email", password="password123"
        )
        service.normalize()
        with self.assertRaises(InvalidEmailFormatException):
            service.validate()

    def test_validate_email_valid(self):
        """Тест валидации валидного email."""
        service = RegisterServiceBase(
            session=self.session, username="testuser", email="test@example.com", password="password123"
        )
        service.normalize()
        try:
            service.validate()
        except InvalidEmailFormatException:
            self.fail("validate() raised InvalidEmailFormatException unexpectedly!")

    def test_validate_password_too_short(self):
        """Тест валидации password слишком короткого."""
        service = RegisterServiceBase(
            session=self.session, username="testuser", email="test@example.com", password="pass123"
        )
        service.normalize()
        with self.assertRaises(InvalidPasswordFormatException):
            service.validate()

    def test_validate_password_too_long(self):
        """Тест валидации password слишком длинного."""
        long_password = "a" * (MAX_PASSWORD_LENGTH + 1) + "1"
        service = RegisterServiceBase(
            session=self.session, username="testuser", email="test@example.com", password=long_password
        )
        service.normalize()
        with self.assertRaises(InvalidPasswordFormatException):
            service.validate()

    def test_validate_password_no_letters(self):
        """Тест валидации password без букв."""
        service = RegisterServiceBase(
            session=self.session, username="testuser", email="test@example.com", password="12345678"
        )
        service.normalize()
        with self.assertRaises(InvalidPasswordFormatException):
            service.validate()

    def test_validate_password_no_digits(self):
        """Тест валидации password без цифр."""
        service = RegisterServiceBase(
            session=self.session, username="testuser", email="test@example.com", password="password"
        )
        service.normalize()
        with self.assertRaises(InvalidPasswordFormatException):
            service.validate()

    def test_validate_password_valid(self):
        """Тест валидации валидного password."""
        service = RegisterServiceBase(
            session=self.session, username="testuser", email="test@example.com", password="password123"
        )
        service.normalize()
        try:
            service.validate()
        except InvalidPasswordFormatException:
            self.fail("validate() raised InvalidPasswordFormatException unexpectedly!")


class TestRegisterServiceMethods(TestCase):
    """Тесты для отдельных методов RegisterService."""

    def setUp(self):
        """Подготовка тестовых данных."""
        self.session = AsyncMock(spec=AsyncSession)

    def _run_async(self, coro):
        """Вспомогательный метод для запуска асинхронного кода."""
        return asyncio.run(coro)

    def test_check_uniqueness_no_conflicts(self):
        """Тест проверки уникальности без конфликтов."""
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        self.session.execute = AsyncMock(return_value=mock_result)

        service = RegisterService(
            session=self.session,
            username="testuser",
            email="test@example.com",
            password="password123",
        )
        service.normalize()

        self._run_async(service._check_uniqueness())
        self.session.execute.assert_called_once()

    def test_check_uniqueness_username_exists(self):
        """Тест проверки уникальности при существующем username."""
        from app.db.models.tables import User

        existing_user = Mock(spec=User)
        existing_user.username = "testuser"
        existing_user.email = "other@example.com"

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [existing_user]
        self.session.execute = AsyncMock(return_value=mock_result)

        service = RegisterService(
            session=self.session,
            username="testuser",
            email="test@example.com",
            password="password123",
        )
        service.normalize()

        with self.assertRaises(UsernameAlreadyExistsException):
            self._run_async(service._check_uniqueness())

    def test_check_uniqueness_email_exists(self):
        """Тест проверки уникальности при существующем email."""
        from app.db.models.tables import User

        existing_user = Mock(spec=User)
        existing_user.username = "otheruser"
        existing_user.email = "test@example.com"

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [existing_user]
        self.session.execute = AsyncMock(return_value=mock_result)

        service = RegisterService(
            session=self.session,
            username="testuser",
            email="test@example.com",
            password="password123",
        )
        service.normalize()

        with self.assertRaises(EmailAlreadyExistsException):
            self._run_async(service._check_uniqueness())

    def test_create_verification_code(self):
        """Тест создания кода подтверждения."""
        user_id = uuid4()
        added_objects = []

        def mock_add(obj):
            added_objects.append(obj)

        self.session.add = Mock(side_effect=mock_add)

        service = RegisterService(
            session=self.session,
            username="testuser",
            email="test@example.com",
            password="password123",
        )

        code = self._run_async(service._create_verification_code(user_id))

        self.assertIsInstance(code, str)
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())
        self.session.add.assert_called_once()

        self.assertEqual(len(added_objects), 1)
        verification_code_obj = added_objects[0]
        self.assertEqual(verification_code_obj.user_id, user_id)
        self.assertEqual(verification_code_obj.code, code)
        self.assertIsNotNone(verification_code_obj.expires_at)

    def test_create_user_with_code(self):
        """Тест создания пользователя и кода подтверждения."""
        from app.db.models.tables import User

        user_id = uuid4()
        created_user = None

        def mock_add(obj):
            nonlocal created_user
            if isinstance(obj, User):
                created_user = obj
                obj.id = user_id

        self.session.add = Mock(side_effect=mock_add)
        self.session.flush = AsyncMock()

        service = RegisterService(
            session=self.session,
            username="testuser",
            email="test@example.com",
            password="password123",
        )
        service.normalize()

        user, code = self._run_async(service._create_user_with_code())

        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertFalse(user.is_verified)
        self.assertIsNotNone(user.password)
        self.assertEqual(user.id, user_id)
        self.assertIsInstance(code, str)
        self.assertEqual(len(code), 6)
        self.assertEqual(self.session.add.call_count, 2)
        self.session.flush.assert_awaited_once()

    def test_send_verification_email_success(self):
        """Тест успешной отправки email."""
        from app.services.email import EmailService

        service = RegisterService(
            session=self.session,
            username="testuser",
            email="test@example.com",
            password="password123",
        )

        with unittest.mock.patch.object(EmailService, "send_verification_code", new_callable=AsyncMock) as mock_send:
            self._run_async(service._send_verification_email("test@example.com", "123456"))
            mock_send.assert_awaited_once_with(to_email="test@example.com", code="123456")

    def test_send_verification_email_failure(self):
        """Тест ошибки отправки email."""
        from app.services.email import EmailService

        service = RegisterService(
            session=self.session,
            username="testuser",
            email="test@example.com",
            password="password123",
        )

        with unittest.mock.patch.object(EmailService, "send_verification_code", new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = Exception("SMTP error")
            with self.assertRaises(EmailSendFailedException):
                self._run_async(service._send_verification_email("test@example.com", "123456"))


class TestRegisterServiceExec(TestCase):
    """Тесты для метода exec с реальной БД."""

    def setUp(self):
        """Подготовка тестовых данных."""
        self.logger = Mock()
        self.database_url = "sqlite+aiosqlite:///:memory:"

    def _run_async(self, coro):
        """Вспомогательный метод для запуска асинхронного кода."""
        return asyncio.run(coro)

    def _patch_server_defaults_for_sqlite(self):
        """Патч server_default для работы с SQLite."""
        original_user_created = User.created_at.property.columns[0].server_default
        original_user_updated = User.updated_at.property.columns[0].server_default
        original_code_created = VerificationCode.created_at.property.columns[0].server_default

        User.created_at.property.columns[0].server_default = None
        User.updated_at.property.columns[0].server_default = None
        VerificationCode.created_at.property.columns[0].server_default = None

        return original_user_created, original_user_updated, original_code_created

    def _restore_server_defaults(self, original_user_created, original_user_updated, original_code_created):
        """Восстановление оригинальных server_default."""
        User.created_at.property.columns[0].server_default = original_user_created
        User.updated_at.property.columns[0].server_default = original_user_updated
        VerificationCode.created_at.property.columns[0].server_default = original_code_created

    def test_exec_success(self):
        """Тест успешной регистрации пользователя с реальной БД."""
        from app.services.email import EmailService

        manager = ManagerAsync(logger=self.logger, database_url=self.database_url)

        originals = self._patch_server_defaults_for_sqlite()

        try:

            async def _test_session():
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                async with manager.get_session() as session:
                    service = RegisterService(
                        session=session,
                        username="testuser",
                        email="test@example.com",
                        password="password123",
                    )
                    user = await service.exec()

                    self.assertIsNotNone(user)
                    self.assertEqual(user.username, "testuser")
                    self.assertEqual(user.email, "test@example.com")
                    self.assertFalse(user.is_verified)
                    self.assertIsNotNone(user.password)
                    self.assertIsNotNone(user.id)

                async with manager.get_session() as session:
                    result = await session.execute(
                        text("SELECT COUNT(*) FROM users WHERE username = :username"), {"username": "testuser"}
                    )
                    count = result.scalar()
                    self.assertEqual(count, 1)

                    result = await session.execute(
                        text("""
                            SELECT COUNT(*) FROM verification_codes vc
                            JOIN users u ON vc.user_id = u.id
                            WHERE u.username = :username
                        """),
                        {"username": "testuser"},
                    )
                    count = result.scalar()
                    self.assertEqual(count, 1)

            with unittest.mock.patch.object(EmailService, "send_verification_code", new_callable=AsyncMock):
                self._run_async(_test_session())
            self.logger.error.assert_not_called()
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
                    service1 = RegisterService(
                        session=session,
                        username="testuser",
                        email="test1@example.com",
                        password="password123",
                    )
                    await service1.exec()

                async with manager.get_session() as session:
                    service2 = RegisterService(
                        session=session,
                        username="testuser",
                        email="test2@example.com",
                        password="password123",
                    )
                    with self.assertRaises(UsernameAlreadyExistsException):
                        await service2.exec()

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
                    service1 = RegisterService(
                        session=session,
                        username="testuser1",
                        email="test@example.com",
                        password="password123",
                    )
                    await service1.exec()

                async with manager.get_session() as session:
                    service2 = RegisterService(
                        session=session,
                        username="testuser2",
                        email="test@example.com",
                        password="password123",
                    )
                    with self.assertRaises(EmailAlreadyExistsException):
                        await service2.exec()

            with unittest.mock.patch.object(EmailService, "send_verification_code", new_callable=AsyncMock):
                self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_invalid_username(self):
        """Тест регистрации с неверным username."""
        manager = ManagerAsync(logger=self.logger, database_url=self.database_url)

        originals = self._patch_server_defaults_for_sqlite()

        try:

            async def _test_session():
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                async with manager.get_session() as session:
                    service = RegisterService(
                        session=session,
                        username="ab",
                        email="test@example.com",
                        password="password123",
                    )
                    with self.assertRaises(InvalidUsernameFormatException):
                        await service.exec()

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_invalid_email(self):
        """Тест регистрации с неверным email."""
        manager = ManagerAsync(logger=self.logger, database_url=self.database_url)

        originals = self._patch_server_defaults_for_sqlite()

        try:

            async def _test_session():
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                async with manager.get_session() as session:
                    service = RegisterService(
                        session=session,
                        username="testuser",
                        email="invalid-email",
                        password="password123",
                    )
                    with self.assertRaises(InvalidEmailFormatException):
                        await service.exec()

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_invalid_password(self):
        """Тест регистрации с неверным password."""
        manager = ManagerAsync(logger=self.logger, database_url=self.database_url)

        originals = self._patch_server_defaults_for_sqlite()

        try:

            async def _test_session():
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                async with manager.get_session() as session:
                    service = RegisterService(
                        session=session,
                        username="testuser",
                        email="test@example.com",
                        password="short",
                    )
                    with self.assertRaises(InvalidPasswordFormatException):
                        await service.exec()

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_email_send_failure(self):
        """Тест регистрации с ошибкой отправки email."""
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
                        service = RegisterService(
                            session=session,
                            username="testuser",
                            email="test@example.com",
                            password="password123",
                        )
                        with self.assertRaises(EmailSendFailedException):
                            await service.exec()

                        result = await session.execute(text("SELECT COUNT(*) FROM users"))
                        count = result.scalar()
                        self.assertEqual(count, 0)

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)
