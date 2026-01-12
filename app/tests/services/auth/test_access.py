import asyncio
from datetime import datetime, timedelta, timezone
from unittest import TestCase
from unittest.mock import Mock
from uuid import uuid4

from jose import jwt

from app.config import JWT_ALGORITHM, JWT_SECRET_KEY
from app.db.models.base import Base
from app.db.models.tables import User
from app.db.session.manager import ManagerAsync
from app.services.auth.common import create_tokens
from app.services.auth.exceptions import TokenExpiredException, TokenInvalidException, UserNotFoundException
from app.services.auth.access import authenticate_access_token


class TestAuthenticateAccessToken(TestCase):
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

    def _make_access_token(self, *, sub: str, exp: datetime) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": sub,
            "type": "access",
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    def _make_refresh_token(self, *, sub: str, exp: datetime) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": sub,
            "type": "refresh",
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    def test_happy_path_returns_user(self):
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

                access, _ = create_tokens(user.id)

                async with manager.get_session() as session:
                    user_out = await authenticate_access_token(session, access)

                self.assertEqual(user_out.id, user.id)

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_raises_token_invalid_for_non_jwt(self):
        async def _test():
            manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
            engine = manager.get_engine()
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            async with manager.get_session() as session:
                with self.assertRaises(TokenInvalidException):
                    await authenticate_access_token(session, "not-a-jwt")

        self._run_async(_test())

    def test_raises_token_expired_for_expired_access_token(self):
        async def _test():
            manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
            engine = manager.get_engine()
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            expired = datetime.now(timezone.utc) - timedelta(minutes=1)
            token = self._make_access_token(sub=str(uuid4()), exp=expired)

            async with manager.get_session() as session:
                with self.assertRaises(TokenExpiredException):
                    await authenticate_access_token(session, token)

        self._run_async(_test())

    def test_raises_token_invalid_if_refresh_token_passed(self):
        async def _test():
            manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
            engine = manager.get_engine()
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            exp = datetime.now(timezone.utc) + timedelta(days=1)
            refresh = self._make_refresh_token(sub=str(uuid4()), exp=exp)

            async with manager.get_session() as session:
                with self.assertRaises(TokenInvalidException):
                    await authenticate_access_token(session, refresh)

        self._run_async(_test())

    def test_raises_token_invalid_if_sub_is_not_uuid(self):
        async def _test():
            manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
            engine = manager.get_engine()
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            exp = datetime.now(timezone.utc) + timedelta(minutes=5)
            token = self._make_access_token(sub="not-a-uuid", exp=exp)

            async with manager.get_session() as session:
                with self.assertRaises(TokenInvalidException):
                    await authenticate_access_token(session, token)

        self._run_async(_test())

    def test_raises_user_not_found_if_user_does_not_exist(self):
        async def _test():
            manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
            engine = manager.get_engine()
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            exp = datetime.now(timezone.utc) + timedelta(minutes=5)
            user_id = uuid4()
            token = self._make_access_token(sub=str(user_id), exp=exp)

            async with manager.get_session() as session:
                with self.assertRaises(UserNotFoundException):
                    await authenticate_access_token(session, token)

        self._run_async(_test())
