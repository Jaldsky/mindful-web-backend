import asyncio
from datetime import datetime, timedelta, timezone
from unittest import TestCase
from unittest.mock import Mock

from sqlalchemy import text

from app.db.models.base import Base
from app.db.models.tables import User, VerificationCode
from app.db.session.manager import ManagerAsync
from app.services.auth.queries import (
    fetch_active_verification_code_row,
    fetch_unused_verification_code_row_by_user_and_code,
    fetch_user_by_email,
    fetch_user_by_id,
    fetch_user_by_username,
    fetch_users_by_username_or_email,
    fetch_user_with_active_verification_code_by_email,
    fetch_user_with_latest_unused_verification_code_by_email,
    update_verification_code_last_sent_at,
)


class TestAuthQueries(TestCase):
    """Тесты функций queries.py (работа с БД)."""

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

    def test_fetch_user_by_email_returns_none_for_deleted_user(self):
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
                        username="testuser",
                        email="test@example.com",
                        password="hash",
                        is_verified=False,
                        created_at=now,
                        updated_at=now,
                        deleted_at=now,
                    )
                    session.add(user)
                    await session.commit()

                async with manager.get_session() as session:
                    found = await fetch_user_by_email(session, "test@example.com")
                    self.assertIsNone(found)

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_fetch_user_by_id_returns_user(self):
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
                        username="testuser",
                        email="test@example.com",
                        password="hash",
                        is_verified=False,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(user)
                    await session.commit()
                    user_id = user.id

                async with manager.get_session() as session:
                    found = await fetch_user_by_id(session, user_id)
                    self.assertIsNotNone(found)
                    self.assertEqual(found.id, user_id)

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_fetch_user_by_id_returns_none_for_deleted_user(self):
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
                        username="testuser",
                        email="test@example.com",
                        password="hash",
                        is_verified=False,
                        created_at=now,
                        updated_at=now,
                        deleted_at=now,
                    )
                    session.add(user)
                    await session.commit()
                    user_id = user.id

                async with manager.get_session() as session:
                    found = await fetch_user_by_id(session, user_id)
                    self.assertIsNone(found)

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_fetch_user_by_username_returns_user(self):
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
                    found = await fetch_user_by_username(session, "testuser")
                    self.assertIsNotNone(found)
                    self.assertEqual(found.username, "testuser")

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_fetch_user_by_username_returns_none_for_deleted_user(self):
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
                        username="testuser",
                        email="test@example.com",
                        password="hash",
                        is_verified=False,
                        created_at=now,
                        updated_at=now,
                        deleted_at=now,
                    )
                    session.add(user)
                    await session.commit()

                async with manager.get_session() as session:
                    found = await fetch_user_by_username(session, "testuser")
                    self.assertIsNone(found)

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_fetch_users_by_username_or_email_excludes_deleted(self):
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test():
                manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                now = datetime.now(timezone.utc)
                async with manager.get_session() as session:
                    session.add(
                        User(
                            username="u1",
                            email="u1@example.com",
                            password="hash",
                            is_verified=False,
                            created_at=now,
                            updated_at=now,
                        )
                    )
                    session.add(
                        User(
                            username="u2",
                            email="u2@example.com",
                            password="hash",
                            is_verified=False,
                            created_at=now,
                            updated_at=now,
                            deleted_at=now,
                        )
                    )
                    await session.commit()

                async with manager.get_session() as session:
                    users = await fetch_users_by_username_or_email(session, "u2", "u1@example.com")
                    emails = sorted([u.email for u in users])
                    self.assertEqual(emails, ["u1@example.com"])

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_fetch_active_verification_code_row_returns_latest_active(self):
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
                            expires_at=now - timedelta(minutes=1),
                            used_at=None,
                            created_at=now - timedelta(minutes=2),
                        )
                    )
                    session.add(
                        VerificationCode(
                            user_id=user.id,
                            code="222222",
                            expires_at=now + timedelta(minutes=10),
                            used_at=None,
                            created_at=now - timedelta(minutes=1),
                        )
                    )
                    session.add(
                        VerificationCode(
                            user_id=user.id,
                            code="333333",
                            expires_at=now + timedelta(minutes=10),
                            used_at=None,
                            created_at=now,
                        )
                    )
                    await session.commit()

                async with manager.get_session() as session:
                    row = await fetch_active_verification_code_row(session, user.id, now)
                    self.assertIsNotNone(row)
                    self.assertEqual(row.code, "333333")

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_fetch_unused_verification_code_row_by_user_and_code_ignores_used(self):
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
                            expires_at=now + timedelta(minutes=10),
                            used_at=now,
                            created_at=now,
                        )
                    )
                    session.add(
                        VerificationCode(
                            user_id=user.id,
                            code="123456",
                            expires_at=now + timedelta(minutes=10),
                            used_at=None,
                            created_at=now - timedelta(minutes=1),
                        )
                    )
                    await session.commit()

                async with manager.get_session() as session:
                    row = await fetch_unused_verification_code_row_by_user_and_code(session, user.id, "123456")
                    self.assertIsNotNone(row)
                    self.assertIsNone(row.used_at)

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_update_verification_code_last_sent_at(self):
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
                        username="testuser",
                        email="test@example.com",
                        password="hash",
                        is_verified=False,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(user)
                    await session.flush()
                    row = VerificationCode(
                        user_id=user.id,
                        code="123456",
                        expires_at=now + timedelta(minutes=10),
                        used_at=None,
                        last_sent_at=None,
                        created_at=now,
                    )
                    session.add(row)
                    await session.commit()
                    verification_code_id = row.id

                touch_at = now + timedelta(seconds=5)
                async with manager.get_session() as session:
                    await update_verification_code_last_sent_at(session, verification_code_id, touch_at)
                    await session.commit()

                async with manager.get_session() as session:
                    result = await session.execute(
                        text("SELECT last_sent_at FROM verification_codes WHERE id = :id"),
                        {"id": verification_code_id},
                    )
                    self.assertIsNotNone(result.scalar())

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_fetch_user_with_active_verification_code_by_email(self):
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
                            expires_at=now + timedelta(minutes=10),
                            used_at=None,
                            created_at=now,
                        )
                    )
                    await session.commit()

                async with manager.get_session() as session:
                    user_row, code_row = await fetch_user_with_active_verification_code_by_email(
                        session, "test@example.com", now
                    )
                    self.assertIsNotNone(user_row)
                    self.assertIsNotNone(code_row)
                    self.assertEqual(user_row.email, "test@example.com")
                    self.assertEqual(code_row.code, "123456")

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_fetch_user_with_latest_unused_verification_code_by_email(self):
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
                            expires_at=now + timedelta(minutes=10),
                            used_at=None,
                            created_at=now - timedelta(minutes=1),
                        )
                    )
                    session.add(
                        VerificationCode(
                            user_id=user.id,
                            code="222222",
                            expires_at=now + timedelta(minutes=10),
                            used_at=None,
                            created_at=now,
                        )
                    )
                    await session.commit()

                async with manager.get_session() as session:
                    user_row, code_row = await fetch_user_with_latest_unused_verification_code_by_email(
                        session, "test@example.com"
                    )
                    self.assertIsNotNone(user_row)
                    self.assertIsNotNone(code_row)
                    self.assertEqual(user_row.email, "test@example.com")
                    self.assertEqual(code_row.code, "222222")

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)
