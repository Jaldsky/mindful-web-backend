import bcrypt
import asyncio
from datetime import datetime, timedelta, timezone
from unittest import TestCase
from unittest.mock import Mock
from uuid import uuid4

from jose import jwt

from app.config import JWT_ALGORITHM, JWT_SECRET_KEY
from app.services.auth.common import (
    create_tokens,
    decode_token,
    generate_verification_code,
    hash_password,
    verify_password,
)
from app.services.auth.common import get_unverified_user_by_email
from app.services.auth.exceptions import (
    EmailAlreadyVerifiedException,
    TokenExpiredException,
    TokenInvalidException,
    UserNotFoundException,
)
from app.db.models.base import Base
from app.db.models.tables import User
from app.db.session.manager import ManagerAsync


class TestAuthCommon(TestCase):
    """Тесты общих утилит auth-сервиса."""

    def test_generate_verification_code_default(self):
        """Код по умолчанию: 6 цифр."""
        code = generate_verification_code()
        self.assertIsInstance(code, str)
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())

    def test_generate_verification_code_custom_length(self):
        """Код заданной длины: только цифры."""
        code = generate_verification_code(length=10)
        self.assertEqual(len(code), 10)
        self.assertTrue(code.isdigit())

    def test_hash_password_can_be_verified_by_bcrypt(self):
        """Хеш bcrypt должен проверяться функцией checkpw."""
        password = "password123"
        hashed = hash_password(password, rounds=4)  # ускоряем тест
        self.assertIsInstance(hashed, str)
        self.assertTrue(hashed.startswith("$2"))
        self.assertTrue(bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8")))

    def test_verify_password_true_for_correct_password(self):
        password = "password123"
        hashed = hash_password(password, rounds=4)
        self.assertTrue(verify_password(password, hashed))

    def test_verify_password_false_for_wrong_password(self):
        hashed = hash_password("password123", rounds=4)
        self.assertFalse(verify_password("wrongpass", hashed))

    def test_create_tokens_rotates_jti(self):
        """Повторный выпуск токенов в ту же секунду должен давать разные JWT (за счёт jti)."""
        user_id = uuid4()
        _a1, r1 = create_tokens(user_id)
        _a2, r2 = create_tokens(user_id)
        self.assertNotEqual(r1, r2)

    def test_create_tokens_returns_access_and_refresh(self):
        user_id = uuid4()
        access, refresh = create_tokens(user_id)
        self.assertIsInstance(access, str)
        self.assertIsInstance(refresh, str)
        self.assertNotEqual(access, refresh)

        access_payload = decode_token(access)
        refresh_payload = decode_token(refresh)
        self.assertEqual(access_payload.get("type"), "access")
        self.assertEqual(refresh_payload.get("type"), "refresh")
        self.assertEqual(access_payload.get("sub"), str(user_id))
        self.assertEqual(refresh_payload.get("sub"), str(user_id))

    def test_decode_token_invalid_raises(self):
        with self.assertRaises(TokenInvalidException):
            decode_token("not-a-jwt")

    def test_decode_token_expired_raises(self):
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(uuid4()),
            "type": "refresh",
            "iat": int(now.timestamp()),
            "exp": int((now - timedelta(minutes=1)).timestamp()),
        }
        expired = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        with self.assertRaises(TokenExpiredException):
            decode_token(expired)


class TestGetUnverifiedUserByEmail(TestCase):
    """Тесты для get_unverified_user_by_email."""

    def setUp(self):
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

    def test_returns_user_when_email_not_verified(self):
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
                    found = await get_unverified_user_by_email(session, "test@example.com")
                    self.assertEqual(found.email, "test@example.com")
                    self.assertFalse(found.is_verified)

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_raises_user_not_found(self):
        originals = self._patch_server_defaults_for_sqlite()
        try:

            async def _test():
                manager = ManagerAsync(logger=self.logger, database_url=self.database_url)
                engine = manager.get_engine()
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                async with manager.get_session() as session:
                    with self.assertRaises(UserNotFoundException):
                        await get_unverified_user_by_email(session, "missing@example.com")

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)

    def test_raises_email_already_verified(self):
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
                    with self.assertRaises(EmailAlreadyVerifiedException):
                        await get_unverified_user_by_email(session, "test@example.com")

            self._run_async(_test())
        finally:
            self._restore_server_defaults(*originals)
