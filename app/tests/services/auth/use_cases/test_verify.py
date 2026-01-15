import asyncio
import unittest
from datetime import datetime, timedelta, timezone
from unittest import TestCase
from unittest.mock import Mock

from sqlalchemy import text

from app.db.models.base import Base
from app.db.models.tables import User, VerificationCode
from app.db.session.manager import ManagerAsync
from app.services.auth import VerifyEmailService
from app.services.auth.exceptions import (
    EmailAlreadyVerifiedException,
    InvalidVerificationCodeFormatException,
    UserNotFoundException,
    VerificationCodeExpiredException,
    VerificationCodeInvalidException,
    TooManyAttemptsException,
)
from app.schemas.auth import VerifyRequestSchema


class TestVerifyEmailServiceExec(TestCase):
    """Тесты для VerifyEmailService.exec с реальной БД."""

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

    def test_exec_success_marks_user_verified_and_code_used(self):
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                now = datetime.now(timezone.utc)
                expires_at = now + timedelta(minutes=10)

                async with manager.get_session() as session:
                    user = User(
                        username="testuser",
                        email="test@example.com",
                        password="hash",
                        is_verified=False,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(user)
                    await session.flush()
                    session.add(
                        VerificationCode(
                            user_id=user.id,
                            code="123456",
                            expires_at=expires_at,
                            used_at=None,
                            created_at=now,
                        )
                    )
                    await session.commit()

                async with manager.get_session() as session:
                    service = VerifyEmailService(session=session, email="test@example.com", code="123456")
                    ok = await service.exec()
                    self.assertIsNone(ok)

                async with manager.get_session() as session:
                    result = await session.execute(
                        text("SELECT is_verified FROM users WHERE email = :email"), {"email": "test@example.com"}
                    )
                    self.assertEqual(bool(result.scalar()), True)
                    result = await session.execute(
                        text(
                            "SELECT used_at FROM verification_codes vc "
                            "JOIN users u ON vc.user_id = u.id "
                            "WHERE u.email = :email AND vc.code = :code"
                        ),
                        {"email": "test@example.com", "code": "123456"},
                    )
                    self.assertIsNotNone(result.scalar())

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_pending_email_applies_new_email(self):
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                now = datetime.now(timezone.utc)
                expires_at = now + timedelta(minutes=10)

                async with manager.get_session() as session:
                    user = User(
                        username="testuser",
                        email="old@example.com",
                        pending_email="new@example.com",
                        password="hash",
                        is_verified=True,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(user)
                    await session.flush()
                    session.add(
                        VerificationCode(
                            user_id=user.id,
                            code="123456",
                            expires_at=expires_at,
                            used_at=None,
                            created_at=now,
                        )
                    )
                    await session.commit()

                async with manager.get_session() as session:
                    service = VerifyEmailService(session=session, email="new@example.com", code="123456")
                    ok = await service.exec()
                    self.assertIsNone(ok)

                async with manager.get_session() as session:
                    refreshed = await session.get(User, user.id)
                    self.assertEqual(refreshed.email, "new@example.com")
                    self.assertIsNone(refreshed.pending_email)
                    self.assertTrue(refreshed.is_verified)

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_user_not_found(self):
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                async with manager.get_session() as session:
                    service = VerifyEmailService(session=session, email="missing@example.com", code="123456")
                    with self.assertRaises(UserNotFoundException):
                        await service.exec()

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_old_pending_email_not_found(self):
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                now = datetime.now(timezone.utc)
                expires_at = now + timedelta(minutes=10)

                async with manager.get_session() as session:
                    user = User(
                        username="testuser",
                        email="old@example.com",
                        pending_email="second@example.com",
                        password="hash",
                        is_verified=True,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(user)
                    await session.flush()
                    session.add(
                        VerificationCode(
                            user_id=user.id,
                            code="123456",
                            expires_at=expires_at,
                            used_at=None,
                            created_at=now,
                        )
                    )
                    await session.commit()

                async with manager.get_session() as session:
                    service = VerifyEmailService(session=session, email="first@example.com", code="123456")
                    with self.assertRaises(UserNotFoundException):
                        await service.exec()

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_email_already_verified(self):
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                now = datetime.now(timezone.utc)
                async with manager.get_session() as session:
                    user = User(
                        username="testuser",
                        email="test@example.com",
                        password="hash",
                        is_verified=True,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(user)
                    await session.commit()

                async with manager.get_session() as session:
                    service = VerifyEmailService(session=session, email="test@example.com", code="123456")
                    with self.assertRaises(EmailAlreadyVerifiedException):
                        await service.exec()

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_code_invalid(self):
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                now = datetime.now(timezone.utc)
                expires_at = now + timedelta(minutes=10)

                async with manager.get_session() as session:
                    user = User(
                        username="testuser",
                        email="test@example.com",
                        password="hash",
                        is_verified=False,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(user)
                    await session.flush()
                    session.add(
                        VerificationCode(
                            user_id=user.id,
                            code="111111",
                            expires_at=expires_at,
                            used_at=None,
                            created_at=now,
                        )
                    )
                    await session.commit()

                async with manager.get_session() as session:
                    service = VerifyEmailService(session=session, email="test@example.com", code="222222")
                    with self.assertRaises(VerificationCodeInvalidException):
                        await service.exec()

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_code_expired(self):
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                now = datetime.now(timezone.utc)
                expires_at = now - timedelta(minutes=1)

                async with manager.get_session() as session:
                    user = User(
                        username="testuser",
                        email="test@example.com",
                        password="hash",
                        is_verified=False,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(user)
                    await session.flush()
                    session.add(
                        VerificationCode(
                            user_id=user.id,
                            code="123456",
                            expires_at=expires_at,
                            used_at=None,
                            created_at=now,
                        )
                    )
                    await session.commit()

                async with manager.get_session() as session:
                    service = VerifyEmailService(session=session, email="test@example.com", code="123456")
                    with self.assertRaises(VerificationCodeExpiredException):
                        await service.exec()

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_code_format_invalid(self):
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                with self.assertRaises(InvalidVerificationCodeFormatException):
                    VerifyRequestSchema(email="test@example.com", code="12ab56")

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_increments_attempts_on_invalid_code(self):
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                now = datetime.now(timezone.utc)
                expires_at = now + timedelta(minutes=10)

                async with manager.get_session() as session:
                    user = User(
                        username="testuser",
                        email="test@example.com",
                        password="hash",
                        is_verified=False,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(user)
                    await session.flush()
                    session.add(
                        VerificationCode(
                            user_id=user.id,
                            code="123456",
                            expires_at=expires_at,
                            used_at=None,
                            attempts=0,
                            created_at=now,
                        )
                    )
                    await session.commit()

                async with manager.get_session() as session:
                    service = VerifyEmailService(session=session, email="test@example.com", code="000000")
                    with self.assertRaises(VerificationCodeInvalidException):
                        await service.exec()

                async with manager.get_session() as session:
                    result = await session.execute(
                        text("SELECT attempts FROM verification_codes WHERE code = '123456'")
                    )
                    self.assertEqual(result.scalar(), 1)

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_reaches_max_attempts_invalidates_code(self):
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                now = datetime.now(timezone.utc)
                expires_at = now + timedelta(minutes=10)

                async with manager.get_session() as session:
                    user = User(
                        username="testuser",
                        email="test@example.com",
                        password="hash",
                        is_verified=False,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(user)
                    await session.flush()
                    session.add(
                        VerificationCode(
                            user_id=user.id,
                            code="123456",
                            expires_at=expires_at,
                            used_at=None,
                            attempts=9,
                            created_at=now,
                        )
                    )
                    await session.commit()

                with unittest.mock.patch("app.services.auth.use_cases.verify.VERIFICATION_CODE_MAX_ATTEMPTS", 10):
                    async with manager.get_session() as session:
                        service = VerifyEmailService(session=session, email="test@example.com", code="000000")
                        with self.assertRaises(TooManyAttemptsException):
                            await service.exec()

                async with manager.get_session() as session:
                    result = await session.execute(
                        text("SELECT attempts, used_at FROM verification_codes WHERE code = '123456'")
                    )
                    row = result.fetchone()
                    self.assertEqual(row[0], 10)
                    self.assertIsNotNone(row[1])

                    result = await session.execute(
                        text("SELECT is_verified FROM users WHERE email = 'test@example.com'")
                    )
                    self.assertEqual(int(bool(result.scalar())), 0)

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_used_code_with_max_attempts_raises_too_many_attempts(self):
        """Тест что при попытке использовать уже инвалидированный код (attempts >= 10) выбрасывается TooManyAttemptsException."""
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                now = datetime.now(timezone.utc)
                expires_at = now + timedelta(minutes=10)

                async with manager.get_session() as session:
                    user = User(
                        username="testuser",
                        email="test@example.com",
                        password="hash",
                        is_verified=False,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(user)
                    await session.flush()
                    session.add(
                        VerificationCode(
                            user_id=user.id,
                            code="123456",
                            expires_at=expires_at,
                            used_at=now - timedelta(minutes=1),
                            attempts=10,
                            created_at=now,
                        )
                    )
                    await session.commit()

                with unittest.mock.patch("app.services.auth.use_cases.verify.VERIFICATION_CODE_MAX_ATTEMPTS", 10):
                    async with manager.get_session() as session:
                        service = VerifyEmailService(session=session, email="test@example.com", code="123456")
                        with self.assertRaises(TooManyAttemptsException):
                            await service.exec()

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_used_code_with_low_attempts_raises_invalid(self):
        """Тест что при попытке использовать уже использованный код (но attempts < 10) выбрасывается VerificationCodeInvalidException."""
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                now = datetime.now(timezone.utc)
                expires_at = now + timedelta(minutes=10)

                async with manager.get_session() as session:
                    user = User(
                        username="testuser",
                        email="test@example.com",
                        password="hash",
                        is_verified=False,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(user)
                    await session.flush()
                    session.add(
                        VerificationCode(
                            user_id=user.id,
                            code="123456",
                            expires_at=expires_at,
                            used_at=now - timedelta(minutes=1),
                            attempts=3,
                            created_at=now,
                        )
                    )
                    await session.commit()

                async with manager.get_session() as session:
                    service = VerifyEmailService(session=session, email="test@example.com", code="123456")
                    with self.assertRaises(VerificationCodeInvalidException):
                        await service.exec()

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)
