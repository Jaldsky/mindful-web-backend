import asyncio
from datetime import datetime, timezone
from unittest import TestCase
from unittest.mock import Mock
from uuid import uuid4

from app.db.models.base import Base
from app.db.models.tables import User
from app.db.session.manager import ManagerAsync
from app.services.auth.exceptions import UserNotFoundException
from app.services.user.use_cases.profile import ProfileService, ProfileData


class TestProfileService(TestCase):
    def setUp(self) -> None:
        self.logger = Mock()
        self.database_url = "sqlite+aiosqlite:///:memory:"

    def _run_async(self, coro):
        return asyncio.run(coro)

    def _patch_server_defaults_for_sqlite(self):
        original_user_created = User.created_at.property.columns[0].server_default
        original_user_updated = User.updated_at.property.columns[0].server_default
        User.created_at.property.columns[0].server_default = None
        User.updated_at.property.columns[0].server_default = None
        return original_user_created, original_user_updated

    def _restore_server_defaults(self, original_user_created, original_user_updated):
        User.created_at.property.columns[0].server_default = original_user_created
        User.updated_at.property.columns[0].server_default = original_user_updated

    def test_profile_returns_username_and_email(self):
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
                        is_verified=True,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(user)
                    await session.commit()

                async with manager.get_session() as session:
                    profile = await ProfileService(session=session, user_id=user.id).exec()

                self.assertIsInstance(profile, ProfileData)
                self.assertEqual(profile.username, "testuser")
                self.assertEqual(profile.email, "test@example.com")

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_profile_raises_user_not_found(self):
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test():
                manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                async with manager.get_session() as session:
                    with self.assertRaises(UserNotFoundException):
                        await ProfileService(session=session, user_id=uuid4()).exec()

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)
