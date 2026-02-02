import asyncio
from unittest import TestCase
from unittest.mock import patch, AsyncMock
from fastapi.security import HTTPAuthorizationCredentials
from starlette.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession

from types import SimpleNamespace

from app.api.dependencies import get_accept_language, get_db_session, _extract_access_token
from app.services.auth.constants import AUTH_ACCESS_COOKIE_NAME
from app.db.session.provider import Provider


class TestGetDbSession(TestCase):
    def _run_async(self, coro):
        """Вспомогательный метод для запуска асинхронного кода."""
        return asyncio.run(coro)

    @patch.object(Provider, "async_manager")
    def test_valid_session_returned(self, mock_manager_class):
        """Успешное получение сессии из менеджера."""
        mock_session = AsyncMock(spec=AsyncSession)

        mock_session_context = AsyncMock()
        mock_session_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_context.__aexit__ = AsyncMock(return_value=None)

        mock_manager_class.get_session.return_value = mock_session_context

        async def test_coro():
            gen = get_db_session()
            session = await gen.__anext__()
            self.assertIs(session, mock_session)
            self.assertIsInstance(session, AsyncSession)

            with self.assertRaises(StopAsyncIteration):
                await gen.__anext__()

        self._run_async(test_coro())

    @patch.object(Provider, "async_manager")
    def test_session_is_yielded_only_once(self, mock_manager_class):
        """Генератор должен выдавать ровно одну сессию."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_context = AsyncMock()
        mock_session_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_context.__aexit__ = AsyncMock()
        mock_manager_class.get_session.return_value = mock_session_context

        async def test_coro():
            gen = get_db_session()
            session1 = await gen.__anext__()
            self.assertIs(session1, mock_session)

            with self.assertRaises(StopAsyncIteration):
                await gen.__anext__()

        self._run_async(test_coro())

    def test_function_is_generator(self):
        """Функция должна быть асинхронным генератором."""
        gen = get_db_session()
        self.assertTrue(hasattr(gen, "__aiter__"))
        self.assertTrue(hasattr(gen, "__anext__"))


class TestGetAcceptLanguage(TestCase):
    """Тесты для dependency get_accept_language (Header Accept-Language + схема внутри)."""

    def test_returns_default_and_sets_locale_when_no_header(self):
        """Без заголовка (None) возвращается en и request.state.locale = en."""
        request = SimpleNamespace(state=SimpleNamespace())
        result = get_accept_language(request, None)
        self.assertEqual(result, "en")
        self.assertEqual(request.state.locale, "en")

    def test_returns_ru_and_sets_locale(self):
        """Заголовок ru — возвращается ru и request.state.locale = ru."""
        request = SimpleNamespace(state=SimpleNamespace())
        result = get_accept_language(request, "ru")
        self.assertEqual(result, "ru")
        self.assertEqual(request.state.locale, "ru")

    def test_normalizes_en_us_to_en(self):
        """Заголовок en-US нормализуется в en (схема внутри dependency)."""
        request = SimpleNamespace(state=SimpleNamespace())
        result = get_accept_language(request, "en-US")
        self.assertEqual(result, "en")
        self.assertEqual(request.state.locale, "en")


class TestExtractAccessToken(TestCase):
    def test_prefers_bearer_credentials(self):
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="header-token")
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/",
                "headers": [(b"cookie", f"{AUTH_ACCESS_COOKIE_NAME}=cookie-token".encode())],
            }
        )
        result = _extract_access_token(credentials, request)
        self.assertEqual(result, "header-token")

    def test_falls_back_to_cookie(self):
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/",
                "headers": [(b"cookie", f"{AUTH_ACCESS_COOKIE_NAME}=cookie-token".encode())],
            }
        )
        result = _extract_access_token(None, request)
        self.assertEqual(result, "cookie-token")

    def test_returns_none_without_header_or_cookie(self):
        request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})
        result = _extract_access_token(None, request)
        self.assertIsNone(result)
