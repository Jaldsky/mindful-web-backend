import asyncio
from unittest import TestCase
from unittest.mock import patch
from uuid import UUID

from app.services.auth.common import decode_token
from app.services.auth.exceptions import AuthServiceException
from app.services.auth.use_cases import AnonymousService


class TestAnonymousService(TestCase):
    def _run_async(self, coro):
        return asyncio.run(coro)

    def test_exec_returns_anon_id_and_token(self):
        async def _test():
            service = AnonymousService()
            anon_id, anon_token = await service.exec()

            UUID(str(anon_id))
            payload = decode_token(anon_token)
            self.assertEqual(payload.get("type"), "anon")
            self.assertEqual(payload.get("sub"), str(anon_id))

        self._run_async(_test())

    def test_exec_raises_when_uuid_generation_fails(self):
        async def _test():
            service = AnonymousService()
            with patch("app.services.auth.use_cases.anonymous.uuid4", side_effect=Exception("boom")):
                with self.assertRaises(AuthServiceException) as ctx:
                    await service.exec()

            self.assertEqual(ctx.exception.key, "auth.errors.anon_id_generation_failed")

        self._run_async(_test())

    def test_exec_raises_when_token_creation_fails(self):
        async def _test():
            service = AnonymousService()
            with patch("app.services.auth.use_cases.anonymous.create_anon_token", side_effect=Exception("boom")):
                with self.assertRaises(AuthServiceException) as ctx:
                    await service.exec()

            self.assertEqual(ctx.exception.key, "auth.errors.anon_token_create_failed")

        self._run_async(_test())
