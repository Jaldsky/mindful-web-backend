import asyncio
import unittest
from datetime import datetime, timezone
from unittest import TestCase
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from sqlalchemy import text

from app.db.models.base import Base
from app.db.models.tables import User, VerificationCode
from app.db.session.manager import ManagerAsync
from app import config as app_config
from app.services.auth.exceptions import (
    EmailAlreadyExistsException,
    EmailSendFailedException,
    TooManyAttemptsException,
    UserNotFoundException,
)
from app.services.user.use_cases.update_email import UpdateEmailService


class TestUpdateEmailService(TestCase):
    def setUp(self) -> None:
        self.logger = Mock()
        self.database_url = "sqlite+aiosqlite:///:memory:"

    def _run_async(self, coro):
        return asyncio.run(coro)

    def _patch_server_defaults_for_sqlite(self):
        original_user_created = User.created_at.property.columns[0].server_default
        original_user_updated = User.updated_at.property.columns[0].server_default
        original_code_created = VerificationCode.created_at.property.columns[0].server_default
        original_verification_cooldown = app_config.VERIFICATION_CODE_REQUEST_COOLDOWN_SECONDS
        User.created_at.property.columns[0].server_default = None
        User.updated_at.property.columns[0].server_default = None
        VerificationCode.created_at.property.columns[0].server_default = None
        app_config.VERIFICATION_CODE_REQUEST_COOLDOWN_SECONDS = 0
        return (
            original_user_created,
            original_user_updated,
            original_code_created,
            original_verification_cooldown,
        )

    def _restore_server_defaults(
        self, original_user_created, original_user_updated, original_code_created, original_verification_cooldown
    ):
        User.created_at.property.columns[0].server_default = original_user_created
        User.updated_at.property.columns[0].server_default = original_user_updated
        VerificationCode.created_at.property.columns[0].server_default = original_code_created
        app_config.VERIFICATION_CODE_REQUEST_COOLDOWN_SECONDS = original_verification_cooldown

    def test_exec_updates_email_and_sends_code(self):
        from app.services.email import EmailService

        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test():
                manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                now = datetime.now(timezone.utc)
                async with manager.get_session() as session:
                    user = User(
                        username="user_one",
                        email="old@example.com",
                        password="hash",
                        is_verified=True,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(user)
                    await session.commit()

                async with manager.get_session() as session:
                    profile = await UpdateEmailService(
                        session=session, user_id=user.id, email="new@example.com"
                    ).exec()

                self.assertEqual(profile.email, "old@example.com")

                async with manager.get_session() as session:
                    refreshed = await session.get(User, user.id)
                    self.assertEqual(refreshed.email, "old@example.com")
                    self.assertEqual(refreshed.pending_email, "new@example.com")
                    self.assertTrue(refreshed.is_verified)
                    result = await session.execute(text("SELECT COUNT(*) FROM verification_codes"))
                    self.assertEqual(result.scalar(), 1)

            with unittest.mock.patch.object(
                EmailService, "send_verification_code", new_callable=AsyncMock
            ) as mock_send:
                self._run_async(_test())
                mock_send.assert_awaited_once_with(to_email="new@example.com", code=unittest.mock.ANY)
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_same_verified_email_noop(self):
        from app.services.email import EmailService

        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test():
                manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                now = datetime.now(timezone.utc)
                async with manager.get_session() as session:
                    user = User(
                        username="user_one",
                        email="same@example.com",
                        password="hash",
                        is_verified=True,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(user)
                    await session.commit()

                async with manager.get_session() as session:
                    profile = await UpdateEmailService(
                        session=session, user_id=user.id, email="same@example.com"
                    ).exec()
                    self.assertEqual(profile.email, "same@example.com")

                async with manager.get_session() as session:
                    refreshed = await session.get(User, user.id)
                    self.assertEqual(refreshed.email, "same@example.com")
                    self.assertIsNone(refreshed.pending_email)
                    self.assertTrue(refreshed.is_verified)
                    result = await session.execute(text("SELECT COUNT(*) FROM verification_codes"))
                    self.assertEqual(result.scalar(), 0)

            with unittest.mock.patch.object(
                EmailService, "send_verification_code", new_callable=AsyncMock
            ) as mock_send:
                self._run_async(_test())
                mock_send.assert_not_awaited()
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_email_already_exists(self):
        from app.services.email import EmailService

        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test():
                manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                now = datetime.now(timezone.utc)
                async with manager.get_session() as session:
                    user1 = User(
                        username="user_one",
                        email="first@example.com",
                        password="hash",
                        is_verified=True,
                        created_at=now,
                        updated_at=now,
                    )
                    user2 = User(
                        username="user_two",
                        email="second@example.com",
                        password="hash",
                        is_verified=True,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(user1)
                    session.add(user2)
                    await session.commit()

                async with manager.get_session() as session:
                    with self.assertRaises(EmailAlreadyExistsException):
                        await UpdateEmailService(session=session, user_id=user1.id, email="second@example.com").exec()

            with unittest.mock.patch.object(EmailService, "send_verification_code", new_callable=AsyncMock):
                self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_email_send_failed(self):
        from app.services.email import EmailService

        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test():
                manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                now = datetime.now(timezone.utc)
                async with manager.get_session() as session:
                    user = User(
                        username="user_one",
                        email="old@example.com",
                        password="hash",
                        is_verified=True,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(user)
                    await session.commit()

                async with manager.get_session() as session:
                    with self.assertRaises(EmailSendFailedException):
                        await UpdateEmailService(session=session, user_id=user.id, email="new@example.com").exec()

                async with manager.get_session() as session:
                    refreshed = await session.get(User, user.id)
                    self.assertEqual(refreshed.email, "old@example.com")
                    self.assertIsNone(refreshed.pending_email)
                    self.assertTrue(refreshed.is_verified)

            with unittest.mock.patch.object(
                EmailService, "send_verification_code", new_callable=AsyncMock
            ) as mock_send:
                mock_send.side_effect = Exception("SMTP error")
                self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_overwrites_pending_email_with_latest(self):
        from app.services.email import EmailService

        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test():
                manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                now = datetime.now(timezone.utc)
                async with manager.get_session() as session:
                    user = User(
                        username="user_one",
                        email="old@example.com",
                        password="hash",
                        is_verified=True,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(user)
                    await session.commit()

                async with manager.get_session() as session:
                    await UpdateEmailService(session=session, user_id=user.id, email="first@example.com").exec()

                async with manager.get_session() as session:
                    await UpdateEmailService(session=session, user_id=user.id, email="second@example.com").exec()

                async with manager.get_session() as session:
                    refreshed = await session.get(User, user.id)
                    self.assertEqual(refreshed.email, "old@example.com")
                    self.assertEqual(refreshed.pending_email, "second@example.com")
                    result = await session.execute(text("SELECT COUNT(*) FROM verification_codes"))
                    self.assertEqual(result.scalar(), 2)

            with unittest.mock.patch.object(EmailService, "send_verification_code", new_callable=AsyncMock):
                self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_rate_limited_for_rapid_requests(self):
        from app.services.email import EmailService

        originals = self._patch_server_defaults_for_sqlite()
        try:
            app_config.VERIFICATION_CODE_REQUEST_COOLDOWN_SECONDS = 60

            async def _test():
                manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                now = datetime.now(timezone.utc)
                async with manager.get_session() as session:
                    user = User(
                        username="user_one",
                        email="old@example.com",
                        password="hash",
                        is_verified=True,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(user)
                    await session.commit()

                async with manager.get_session() as session:
                    await UpdateEmailService(session=session, user_id=user.id, email="first@example.com").exec()

                async with manager.get_session() as session:
                    with self.assertRaises(TooManyAttemptsException):
                        await UpdateEmailService(session=session, user_id=user.id, email="second@example.com").exec()

            with unittest.mock.patch.object(EmailService, "send_verification_code", new_callable=AsyncMock):
                self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_exec_user_not_found(self):
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test():
                manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                async with manager.get_session() as session:
                    with self.assertRaises(UserNotFoundException):
                        await UpdateEmailService(session=session, user_id=uuid4(), email="new@example.com").exec()

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)
