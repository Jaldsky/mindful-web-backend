import asyncio
from datetime import datetime, timezone
from unittest import TestCase
from unittest.mock import Mock

from app.db.models.base import Base
from app.db.models.tables import User
from app.db.session.manager import ManagerAsync
from app.services.auth.common import decode_token, hash_password
from app.services.auth.exceptions import EmailNotVerifiedException, InvalidCredentialsException
from app.services.auth.use_cases import LoginService
from app.schemas.auth import LoginRequestSchema


class TestLoginService(TestCase):
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

    def test_happy_path_returns_tokens(self):
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test():
                manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                now = datetime.now(timezone.utc)
                password = "password123"
                password_hash = hash_password(password, rounds=4)

                async with manager.get_session() as session:
                    user = User(
                        username="testuser",
                        email="test@example.com",
                        password=password_hash,
                        is_verified=True,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(user)
                    await session.commit()

                async with manager.get_session() as session:
                    payload = LoginRequestSchema(username="  TestUser  ", password=password)
                    service = LoginService(session=session, username=payload.username, password=payload.password)
                    user_out, access, refresh = await service.exec()

                self.assertEqual(user_out.username, "testuser")

                access_payload = decode_token(access)
                refresh_payload = decode_token(refresh)
                self.assertEqual(access_payload.get("type"), "access")
                self.assertEqual(refresh_payload.get("type"), "refresh")
                self.assertEqual(access_payload.get("sub"), str(user.id))
                self.assertEqual(refresh_payload.get("sub"), str(user.id))

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_raises_invalid_credentials_when_user_not_found(self):
        async def _test():
            manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
            engine = manager.get_engine()
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            async with manager.get_session() as session:
                service = LoginService(session=session, username="missing", password="password123")
                with self.assertRaises(InvalidCredentialsException):
                    await service.exec()

        self._run_async(_test())

    def test_raises_invalid_credentials_when_password_missing(self):
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
                        password=None,
                        is_verified=True,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(user)
                    await session.commit()

                async with manager.get_session() as session:
                    service = LoginService(session=session, username="testuser", password="password123")
                    with self.assertRaises(InvalidCredentialsException):
                        await service.exec()

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_raises_invalid_credentials_when_password_wrong(self):
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test():
                manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                now = datetime.now(timezone.utc)
                password_hash = hash_password("password123", rounds=4)
                async with manager.get_session() as session:
                    user = User(
                        username="testuser",
                        email="test@example.com",
                        password=password_hash,
                        is_verified=True,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(user)
                    await session.commit()

                async with manager.get_session() as session:
                    service = LoginService(session=session, username="testuser", password="wrongpass")
                    with self.assertRaises(InvalidCredentialsException):
                        await service.exec()

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_raises_email_not_verified(self):
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test():
                manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                now = datetime.now(timezone.utc)
                password = "password123"
                password_hash = hash_password(password, rounds=4)
                async with manager.get_session() as session:
                    user = User(
                        username="testuser",
                        email="test@example.com",
                        password=password_hash,
                        is_verified=False,
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(user)
                    await session.commit()

                async with manager.get_session() as session:
                    service = LoginService(session=session, username="testuser", password=password)
                    with self.assertRaises(EmailNotVerifiedException):
                        await service.exec()

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)
