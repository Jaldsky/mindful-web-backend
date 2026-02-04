import asyncio
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth.common import create_anon_token
from app.services.auth.exceptions import TokenInvalidException
from app.services.auth.use_cases import SessionService


class TestSessionService(TestCase):
    def _run_async(self, coro):
        return asyncio.run(coro)

    def test_exec_returns_authenticated_when_access_token_valid(self):
        async def _test():
            user_id = uuid4()
            session = AsyncMock(spec=AsyncSession)
            service = SessionService()
            with patch(
                "app.services.auth.use_cases.session.authenticate_access_token",
                new=AsyncMock(return_value=SimpleNamespace(id=user_id)),
            ):
                state = await service.exec(
                    session=session,
                    access_token="access",
                    anon_token=None,
                )

            self.assertEqual(state.status, "authenticated")
            self.assertEqual(str(state.user_id), str(user_id))
            self.assertIsNone(state.anon_id)

        self._run_async(_test())

    def test_exec_returns_anonymous_when_anon_token_valid(self):
        async def _test():
            anon_id = uuid4()
            anon_token = create_anon_token(anon_id)
            session = AsyncMock(spec=AsyncSession)
            service = SessionService()
            state = await service.exec(
                session=session,
                access_token=None,
                anon_token=anon_token,
            )
            self.assertEqual(state.status, "anonymous")
            self.assertEqual(str(state.anon_id), str(anon_id))
            self.assertIsNone(state.user_id)

        self._run_async(_test())

    def test_exec_returns_anonymous_when_access_invalid_and_anon_valid(self):
        async def _test():
            anon_id = uuid4()
            anon_token = create_anon_token(anon_id)
            session = AsyncMock(spec=AsyncSession)
            service = SessionService()
            with patch(
                "app.services.auth.use_cases.session.authenticate_access_token",
                new=AsyncMock(side_effect=TokenInvalidException(key="auth.errors.token_invalid")),
            ):
                state = await service.exec(
                    session=session,
                    access_token="bad",
                    anon_token=anon_token,
                )

            self.assertEqual(state.status, "anonymous")
            self.assertEqual(str(state.anon_id), str(anon_id))
            self.assertIsNone(state.user_id)

        self._run_async(_test())

    def test_exec_returns_none_when_tokens_invalid(self):
        async def _test():
            session = AsyncMock(spec=AsyncSession)
            service = SessionService()
            with patch(
                "app.services.auth.use_cases.session.authenticate_access_token",
                new=AsyncMock(side_effect=TokenInvalidException(key="auth.errors.token_invalid")),
            ):
                state = await service.exec(
                    session=session,
                    access_token="bad",
                    anon_token="bad",
                )

            self.assertEqual(state.status, "none")
            self.assertIsNone(state.user_id)
            self.assertIsNone(state.anon_id)

        self._run_async(_test())
