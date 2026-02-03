import asyncio
from datetime import datetime, timedelta, timezone
from unittest import TestCase
from unittest.mock import Mock
from uuid import uuid4

from jose import jwt

from app.db.models.base import Base
from app.db.models.tables import User
from app.db.session.manager import ManagerAsync
from app.services.auth.common import create_tokens, decode_token
from app.services.auth.exceptions import TokenExpiredException, TokenInvalidException, UserNotFoundException
from app.services.auth.use_cases import RefreshTokensService
from app.config import JWT_ALGORITHM, JWT_SECRET_KEY
from app.schemas.auth import RefreshRequestSchema


class TestRefreshTokensService(TestCase):
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

    def _make_expired_refresh_token(self, user_id) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "iat": int(now.timestamp()),
            "exp": int((now - timedelta(minutes=1)).timestamp()),
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    def test_happy_path_rotates_refresh_token(self):
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

                access, refresh = create_tokens(user.id)

                async with manager.get_session() as session:
                    service = RefreshTokensService()
                    new_access, new_refresh = await service.exec(
                        session=session,
                        refresh_token=refresh,
                    )

                self.assertIsInstance(new_access, str)
                self.assertIsInstance(new_refresh, str)
                self.assertNotEqual(new_refresh, refresh)

                access_payload = decode_token(new_access)
                refresh_payload = decode_token(new_refresh)
                self.assertEqual(access_payload.get("type"), "access")
                self.assertEqual(refresh_payload.get("type"), "refresh")
                self.assertEqual(refresh_payload.get("sub"), str(user.id))

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_raises_token_invalid_if_access_token_passed(self):
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

                access, _refresh = create_tokens(user.id)

                async with manager.get_session() as session:
                    service = RefreshTokensService()
                    with self.assertRaises(TokenInvalidException):
                        await service.exec(
                            session=session,
                            refresh_token=access,
                        )

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_raises_user_not_found_when_sub_missing_in_db(self):
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test():
                manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                user_id = uuid4()
                _access, refresh = create_tokens(user_id)

                async with manager.get_session() as session:
                    service = RefreshTokensService()
                    with self.assertRaises(UserNotFoundException):
                        await service.exec(
                            session=session,
                            refresh_token=refresh,
                        )

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_raises_token_invalid_on_garbage_token(self):
        async def _test():
            manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
            engine = manager.get_engine()
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            async with manager.get_session() as session:
                service = RefreshTokensService()
                with self.assertRaises(TokenInvalidException):
                    await service.exec(
                        session=session,
                        refresh_token="not-a-jwt",
                    )

        self._run_async(_test())

    def test_raises_token_expired_on_expired_refresh_token(self):
        async def _test():
            manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
            engine = manager.get_engine()
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            expired_refresh = self._make_expired_refresh_token(uuid4())
            async with manager.get_session() as session:
                service = RefreshTokensService()
                with self.assertRaises(TokenExpiredException):
                    await service.exec(
                        session=session,
                        refresh_token=expired_refresh,
                    )

        self._run_async(_test())

    def test_raises_token_invalid_on_refresh_token_without_sub(self):
        async def _test():
            manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
            engine = manager.get_engine()
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            now = datetime.now(timezone.utc)
            payload = {
                "type": "refresh",
                "iat": int(now.timestamp()),
                "exp": int((now + timedelta(minutes=5)).timestamp()),
            }
            refresh_without_sub = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

            async with manager.get_session() as session:
                service = RefreshTokensService()
                with self.assertRaises(TokenInvalidException):
                    await service.exec(
                        session=session,
                        refresh_token=refresh_without_sub,
                    )

        self._run_async(_test())

    def test_accepts_refresh_token_with_spaces(self):
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

                _access, refresh = create_tokens(user.id)
                refresh_with_spaces = f"  {refresh}  "

                async with manager.get_session() as session:
                    payload = RefreshRequestSchema(refresh_token=refresh_with_spaces)
                    service = RefreshTokensService()
                    new_access, new_refresh = await service.exec(
                        session=session,
                        refresh_token=payload.refresh_token,
                    )

                self.assertIsInstance(new_access, str)
                self.assertIsInstance(new_refresh, str)
                self.assertNotEqual(new_refresh, refresh)

                refresh_payload = decode_token(new_refresh)
                self.assertEqual(refresh_payload.get("type"), "refresh")
                self.assertEqual(refresh_payload.get("sub"), str(user.id))

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)
