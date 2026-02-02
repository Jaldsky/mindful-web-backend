import asyncio
import unittest
from unittest import TestCase
from unittest.mock import AsyncMock, Mock

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.base import Base
from app.db.models.tables import User, VerificationCode
from app.db.session.manager import ManagerAsync
from app.services.auth import ResendVerificationCodeService
from app.services.auth.exceptions import (
    AuthServiceException,
    EmailAlreadyVerifiedException,
    EmailSendFailedException,
    InvalidEmailFormatException,
    TooManyAttemptsException,
    UserNotFoundException,
)
from app.schemas.auth import ResendCodeRequestSchema


class TestResendVerificationCodeServiceMethods(TestCase):
    """Тесты для отдельных методов ResendVerificationCodeService."""

    def setUp(self):
        self.session = AsyncMock(spec=AsyncSession)

    def _run_async(self, coro):
        return asyncio.run(coro)

    def test_create_verification_code(self):
        """Тест создания кода подтверждения."""
        from uuid import uuid4

        user_id = uuid4()
        added_objects: list[object] = []

        def mock_add(obj):
            added_objects.append(obj)

        self.session.add = Mock(side_effect=mock_add)

        service = ResendVerificationCodeService(session=self.session, email="test@example.com")
        code = self._run_async(service._create_verification_code(user_id))

        self.assertIsInstance(code, str)
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())
        self.session.add.assert_called_once()
        self.assertEqual(len(added_objects), 1)

    def test_send_verification_email_failure(self):
        """Тест ошибки отправки email."""
        from app.services.email import EmailService

        service = ResendVerificationCodeService(session=self.session, email="test@example.com")
        with unittest.mock.patch("app.services.auth.use_cases.resend_code.logger"):
            with unittest.mock.patch.object(
                EmailService, "send_verification_code", new_callable=AsyncMock
            ) as mock_send:
                mock_send.side_effect = Exception("SMTP error")
                with self.assertRaises(EmailSendFailedException):
                    self._run_async(service._send_verification_email("test@example.com", "123456"))

    def test_send_verification_email_success(self):
        """Тест успешной отправки email."""
        from app.services.email import EmailService

        service = ResendVerificationCodeService(session=self.session, email="test@example.com")
        with unittest.mock.patch.object(EmailService, "send_verification_code", new_callable=AsyncMock) as mock_send:
            self._run_async(service._send_verification_email("test@example.com", "123456"))
            mock_send.assert_awaited_once_with(to_email="test@example.com", code="123456")


class TestResendVerificationCodeServiceExec(TestCase):
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

    def test_exec_success_creates_code(self):
        from app.services.email import EmailService
        from datetime import datetime, timezone

        manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                async with manager.get_session() as session:
                    now = datetime.now(timezone.utc)
                    user = User(
                        username="testuser",
                        email="test@example.com",
                        password="hash",
                        is_verified=False,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(user)
                    await session.commit()

                with unittest.mock.patch.object(EmailService, "send_verification_code", new_callable=AsyncMock):
                    async with manager.get_session() as session:
                        service = ResendVerificationCodeService(session=session, email="test@example.com")
                        ok = await service.exec()
                        self.assertIsNone(ok)

                async with manager.get_session() as session:
                    result = await session.execute(text("SELECT COUNT(*) FROM verification_codes"))
                    self.assertEqual(result.scalar(), 1)
                    result = await session.execute(text("SELECT last_sent_at IS NOT NULL FROM verification_codes"))
                    self.assertEqual(int(bool(result.scalar())), 1)

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_pending_email_allows_resend(self):
        from app.services.email import EmailService
        from datetime import datetime, timezone

        manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                async with manager.get_session() as session:
                    now = datetime.now(timezone.utc)
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
                    await session.commit()

                with unittest.mock.patch.object(EmailService, "send_verification_code", new_callable=AsyncMock):
                    async with manager.get_session() as session:
                        service = ResendVerificationCodeService(session=session, email="new@example.com")
                        ok = await service.exec()
                        self.assertIsNone(ok)

                async with manager.get_session() as session:
                    result = await session.execute(text("SELECT COUNT(*) FROM verification_codes"))
                    self.assertEqual(result.scalar(), 1)

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_user_not_found(self):
        manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                async with manager.get_session() as session:
                    service = ResendVerificationCodeService(session=session, email="missing@example.com")
                    with self.assertRaises(UserNotFoundException):
                        await service.exec()

                async with manager.get_session() as session:
                    result = await session.execute(text("SELECT COUNT(*) FROM verification_codes"))
                    self.assertEqual(result.scalar(), 0)

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_email_already_verified(self):
        from datetime import datetime, timezone

        manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                async with manager.get_session() as session:
                    now = datetime.now(timezone.utc)
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
                    service = ResendVerificationCodeService(session=session, email="test@example.com")
                    with self.assertRaises(EmailAlreadyVerifiedException):
                        await service.exec()

                async with manager.get_session() as session:
                    result = await session.execute(text("SELECT COUNT(*) FROM verification_codes"))
                    self.assertEqual(result.scalar(), 0)

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_reuses_active_code_and_does_not_create_new(self):
        """Если активный код ещё валиден — сервис должен переиспользовать его и не создавать новый."""
        from app.services.email import EmailService
        from datetime import datetime, timezone, timedelta

        manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                async with manager.get_session() as session:
                    now = datetime.now(timezone.utc)
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

                    code_row = VerificationCode(
                        user_id=user.id,
                        code="111111",
                        expires_at=now + timedelta(minutes=10),
                        used_at=None,
                        last_sent_at=now - timedelta(seconds=120),
                        created_at=now - timedelta(seconds=120),
                    )
                    session.add(code_row)
                    await session.commit()

                with unittest.mock.patch.object(
                    EmailService, "send_verification_code", new_callable=AsyncMock
                ) as mock_send:
                    async with manager.get_session() as session:
                        service = ResendVerificationCodeService(session=session, email="test@example.com")
                        ok = await service.exec()
                        self.assertIsNone(ok)

                    mock_send.assert_awaited_once_with(to_email="test@example.com", code="111111")

                async with manager.get_session() as session:
                    result = await session.execute(text("SELECT COUNT(*) FROM verification_codes"))
                    self.assertEqual(result.scalar(), 1)
                    result = await session.execute(
                        text("SELECT last_sent_at IS NOT NULL FROM verification_codes WHERE code = :code"),
                        {"code": "111111"},
                    )
                    self.assertEqual(int(bool(result.scalar())), 1)

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_expired_code_creates_new_code(self):
        """Если код истёк — активного кода нет, должен быть создан новый код."""
        from app.services.email import EmailService
        from datetime import datetime, timezone, timedelta

        manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                async with manager.get_session() as session:
                    now = datetime.now(timezone.utc)
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

                    expired = VerificationCode(
                        user_id=user.id,
                        code="000000",
                        expires_at=now - timedelta(minutes=1),
                        used_at=None,
                        last_sent_at=now - timedelta(minutes=2),
                        created_at=now - timedelta(minutes=2),
                    )
                    session.add(expired)
                    await session.commit()

                with (
                    unittest.mock.patch(
                        "app.services.auth.use_cases.resend_code.generate_verification_code", return_value="333333"
                    ),
                    unittest.mock.patch.object(
                        EmailService, "send_verification_code", new_callable=AsyncMock
                    ) as mock_send,
                ):
                    async with manager.get_session() as session:
                        service = ResendVerificationCodeService(session=session, email="test@example.com")
                        ok = await service.exec()
                        self.assertIsNone(ok)

                    mock_send.assert_awaited_once_with(to_email="test@example.com", code="333333")

                async with manager.get_session() as session:
                    result = await session.execute(text("SELECT COUNT(*) FROM verification_codes"))
                    self.assertEqual(result.scalar(), 2)
                    result = await session.execute(
                        text("SELECT last_sent_at IS NOT NULL FROM verification_codes WHERE code = :code"),
                        {"code": "333333"},
                    )
                    self.assertEqual(int(bool(result.scalar())), 1)

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_used_code_creates_new_code(self):
        """Если код уже использован (used_at != NULL) — он не активный, должен быть создан новый код."""
        from app.services.email import EmailService
        from datetime import datetime, timezone, timedelta

        manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                async with manager.get_session() as session:
                    now = datetime.now(timezone.utc)
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

                    used = VerificationCode(
                        user_id=user.id,
                        code="999999",
                        expires_at=now + timedelta(minutes=10),
                        used_at=now - timedelta(seconds=1),
                        last_sent_at=now - timedelta(minutes=5),
                        created_at=now - timedelta(minutes=5),
                    )
                    session.add(used)
                    await session.commit()

                with (
                    unittest.mock.patch(
                        "app.services.auth.use_cases.resend_code.generate_verification_code", return_value="444444"
                    ),
                    unittest.mock.patch.object(
                        EmailService, "send_verification_code", new_callable=AsyncMock
                    ) as mock_send,
                ):
                    async with manager.get_session() as session:
                        service = ResendVerificationCodeService(session=session, email="test@example.com")
                        ok = await service.exec()
                        self.assertIsNone(ok)

                    mock_send.assert_awaited_once_with(to_email="test@example.com", code="444444")

                async with manager.get_session() as session:
                    result = await session.execute(text("SELECT COUNT(*) FROM verification_codes"))
                    self.assertEqual(result.scalar(), 2)
                    result = await session.execute(
                        text("SELECT last_sent_at IS NOT NULL FROM verification_codes WHERE code = :code"),
                        {"code": "444444"},
                    )
                    self.assertEqual(int(bool(result.scalar())), 1)

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_rate_limits_too_frequent_resend(self):
        """Если resend вызывается слишком часто — должен быть TooManyAttemptsException."""
        from app.services.email import EmailService
        from datetime import datetime, timezone, timedelta

        manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                async with manager.get_session() as session:
                    now = datetime.now(timezone.utc)
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

                    code_row = VerificationCode(
                        user_id=user.id,
                        code="222222",
                        expires_at=now + timedelta(minutes=10),
                        used_at=None,
                        last_sent_at=now,
                        created_at=now,
                    )
                    session.add(code_row)
                    await session.commit()

                with unittest.mock.patch.object(
                    EmailService, "send_verification_code", new_callable=AsyncMock
                ) as mock_send:
                    async with manager.get_session() as session:
                        service = ResendVerificationCodeService(session=session, email="test@example.com")
                        with self.assertRaises(TooManyAttemptsException):
                            await service.exec()

                    mock_send.assert_not_awaited()

                async with manager.get_session() as session:
                    result = await session.execute(text("SELECT COUNT(*) FROM verification_codes"))
                    self.assertEqual(result.scalar(), 1)

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_invalid_email(self):
        ManagerAsync(logger=self.logger, database_url=self.database_url)
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                with self.assertRaises(InvalidEmailFormatException):
                    ResendCodeRequestSchema(email="bad-email")

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_email_send_failure_rolls_back(self):
        """При ошибке отправки email код уже сохранён в БД."""
        from app.services.email import EmailService
        from datetime import datetime, timezone

        manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                async with manager.get_session() as session:
                    now = datetime.now(timezone.utc)
                    user = User(
                        username="testuser",
                        email="test@example.com",
                        password="hash",
                        is_verified=False,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(user)
                    await session.commit()

                with unittest.mock.patch("app.services.auth.use_cases.resend_code.logger"):
                    with unittest.mock.patch.object(
                        EmailService, "send_verification_code", new_callable=AsyncMock
                    ) as mock_send:
                        mock_send.side_effect = Exception("SMTP error")

                        async with manager.get_session() as session:
                            service = ResendVerificationCodeService(session=session, email="test@example.com")
                            with self.assertRaises(EmailSendFailedException):
                                await service.exec()

                async with manager.get_session() as session:
                    result = await session.execute(text("SELECT COUNT(*) FROM verification_codes"))
                    self.assertEqual(result.scalar(), 1)

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_unexpected_db_stage_error_raises_auth_service_exception_with_specific_message(self):
        """Неожиданная ошибка в DB-стадии должна превращаться в AuthServiceException с DB-stage сообщением."""
        from datetime import datetime, timezone

        manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                async with manager.get_session() as session:
                    now = datetime.now(timezone.utc)
                    user = User(
                        username="testuser",
                        email="test@example.com",
                        password="hash",
                        is_verified=False,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(user)
                    await session.commit()

                async with manager.get_session() as session:
                    service = ResendVerificationCodeService(session=session, email="test@example.com")

                    with unittest.mock.patch("app.services.auth.use_cases.resend_code.logger"):
                        with unittest.mock.patch.object(
                            service, "_pick_or_create_code", new_callable=AsyncMock
                        ) as mock_pick:
                            mock_pick.side_effect = Exception("DB stage boom")
                            with self.assertRaises(AuthServiceException) as ctx:
                                await service.exec()

                    self.assertEqual(ctx.exception.message, "auth.errors.resend_code_db_stage_error")

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_unexpected_email_stage_error_raises_auth_service_exception_with_specific_message(self):
        """Неожиданная ошибка в email-стадии должна превращаться в AuthServiceException с email-stage сообщением."""
        from datetime import datetime, timezone

        manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                async with manager.get_session() as session:
                    now = datetime.now(timezone.utc)
                    user = User(
                        username="testuser",
                        email="test@example.com",
                        password="hash",
                        is_verified=False,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(user)
                    await session.commit()

                async with manager.get_session() as session:
                    service = ResendVerificationCodeService(session=session, email="test@example.com")
                    with unittest.mock.patch("app.services.auth.use_cases.resend_code.logger"):
                        with unittest.mock.patch.object(
                            service, "_send_verification_email", new_callable=AsyncMock
                        ) as mock_send:
                            mock_send.side_effect = Exception("Email stage boom")
                            with self.assertRaises(AuthServiceException) as ctx:
                                await service.exec()

                    self.assertEqual(ctx.exception.message, "auth.errors.resend_code_email_stage_error")

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_last_sent_at_update_failure_does_not_break_success(self):
        """Падение best-effort обновления last_sent_at не должно ломать успешный resend."""
        from app.services.email import EmailService
        from datetime import datetime, timezone

        manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                async with manager.get_session() as session:
                    now = datetime.now(timezone.utc)
                    user = User(
                        username="testuser",
                        email="test@example.com",
                        password="hash",
                        is_verified=False,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(user)
                    await session.commit()

                with unittest.mock.patch.object(EmailService, "send_verification_code", new_callable=AsyncMock):
                    async with manager.get_session() as session:
                        service = ResendVerificationCodeService(session=session, email="test@example.com")
                        with unittest.mock.patch("app.services.auth.use_cases.resend_code.logger"):
                            with unittest.mock.patch.object(
                                service, "_touch_last_sent_at", new_callable=AsyncMock
                            ) as mock_touch:
                                mock_touch.side_effect = Exception("last_sent_at update boom")
                                ok = await service.exec()
                                self.assertIsNone(ok)

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_reached_max_attempts_creates_new_code(self):
        """Если у текущего кода достигнут лимит попыток — должен быть создан новый код."""
        from app.services.email import EmailService
        from datetime import datetime, timezone, timedelta

        manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test_session():
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                async with manager.get_session() as session:
                    now = datetime.now(timezone.utc)
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

                    exhausted = VerificationCode(
                        user_id=user.id,
                        code="555555",
                        expires_at=now + timedelta(minutes=10),
                        used_at=None,
                        attempts=10,
                        last_sent_at=now - timedelta(minutes=5),
                        created_at=now - timedelta(minutes=5),
                    )
                    session.add(exhausted)
                    await session.commit()

                with (
                    unittest.mock.patch("app.services.auth.use_cases.resend_code.VERIFICATION_CODE_MAX_ATTEMPTS", 10),
                    unittest.mock.patch(
                        "app.services.auth.use_cases.resend_code.generate_verification_code", return_value="666666"
                    ),
                    unittest.mock.patch.object(
                        EmailService, "send_verification_code", new_callable=AsyncMock
                    ) as mock_send,
                ):
                    async with manager.get_session() as session:
                        service = ResendVerificationCodeService(session=session, email="test@example.com")
                        ok = await service.exec()
                        self.assertIsNone(ok)

                    mock_send.assert_awaited_once_with(to_email="test@example.com", code="666666")

                async with manager.get_session() as session:
                    result = await session.execute(text("SELECT COUNT(*) FROM verification_codes"))
                    self.assertEqual(result.scalar(), 2)
                    result = await session.execute(text("SELECT code FROM verification_codes WHERE code = '666666'"))
                    self.assertIsNotNone(result.scalar())

            self._run_async(_test_session())
        finally:
            self._restore_server_defaults(*originals)
