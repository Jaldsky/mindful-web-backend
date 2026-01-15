import asyncio
from unittest import TestCase
from unittest.mock import Mock, patch
from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.api.handlers import app_exception_handler, method_not_allowed_handler
from app.api.routes import HEALTHCHECK_PATH, SEND_EVENTS_PATH, USER_PROFILE_PATH
from app.schemas import ErrorCode
from app.schemas.events import SaveEventsMethodNotAllowedSchema
from app.schemas.healthcheck import HealthcheckMethodNotAllowedSchema
from app.schemas.user import ProfileMethodNotAllowedSchema
from app.services.auth.exceptions import TokenExpiredException
from app.api import handlers


class TestMethodNotAllowedHandler(TestCase):
    """Тесты для обработчика ошибок 405 Method Not Allowed."""

    def _run_async(self, coro):
        """Вспомогательный метод для запуска асинхронного кода."""
        return asyncio.run(coro)

    def _create_mock_request(self, path: str) -> Request:
        """Создание мок-объекта Request с указанным путём."""
        mock_request = Mock(spec=Request)
        mock_url = Mock()
        mock_url.path = path
        mock_request.url = mock_url
        return mock_request

    def test_healthcheck_path_returns_correct_schema(self):
        """Обработчик возвращает корректную схему для healthcheck endpoint."""
        request = self._create_mock_request(HEALTHCHECK_PATH)
        exc = Exception("Test exception")

        response = self._run_async(method_not_allowed_handler(request, exc))

        self.assertIsInstance(response, JSONResponse)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        content = response.body.decode("utf-8")
        import json

        data = json.loads(content)
        schema = HealthcheckMethodNotAllowedSchema(**data)
        self.assertEqual(schema.code, ErrorCode.METHOD_NOT_ALLOWED)
        self.assertEqual(schema.message, "Method not allowed. Only GET method is supported for this endpoint.")

    def test_send_events_path_returns_correct_schema(self):
        """Обработчик возвращает корректную схему для send events endpoint."""
        request = self._create_mock_request(SEND_EVENTS_PATH)
        exc = Exception("Test exception")

        response = self._run_async(method_not_allowed_handler(request, exc))

        self.assertIsInstance(response, JSONResponse)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        content = response.body.decode("utf-8")
        import json

        data = json.loads(content)
        schema = SaveEventsMethodNotAllowedSchema(**data)
        self.assertEqual(schema.code, ErrorCode.METHOD_NOT_ALLOWED)
        self.assertEqual(schema.message, "Method not allowed. Only POST method is supported for this endpoint.")

    def test_unknown_path_returns_generic_error(self):
        """Обработчик возвращает общую ошибку для неизвестного пути."""
        request = self._create_mock_request("/api/v1/unknown")
        exc = Exception("Test exception")

        response = self._run_async(method_not_allowed_handler(request, exc))

        self.assertIsInstance(response, JSONResponse)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        content = response.body.decode("utf-8")
        import json

        data = json.loads(content)
        self.assertIn("detail", data)
        self.assertEqual(data["detail"], "Method not allowed")

    def test_user_profile_path_returns_correct_schema(self):
        """Обработчик возвращает корректную схему для user profile endpoint."""
        request = self._create_mock_request(USER_PROFILE_PATH)
        exc = Exception("Test exception")

        response = self._run_async(method_not_allowed_handler(request, exc))

        self.assertIsInstance(response, JSONResponse)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        content = response.body.decode("utf-8")
        import json

        data = json.loads(content)
        schema = ProfileMethodNotAllowedSchema(**data)
        self.assertEqual(schema.code, ErrorCode.METHOD_NOT_ALLOWED)


class TestAppExceptionHandler(TestCase):
    """Тесты для обработчика AppException."""

    def _run_async(self, coro):
        """Вспомогательный метод для запуска асинхронного кода."""
        return asyncio.run(coro)

    def _create_mock_request(self, path: str) -> Request:
        """Создание мок-объекта Request с указанным путём."""
        mock_request = Mock(spec=Request)
        mock_url = Mock()
        mock_url.path = path
        mock_request.url = mock_url
        return mock_request

    def test_clears_cookies_on_token_expired(self):
        request = self._create_mock_request("/api/v1/user/profile")
        exc = TokenExpiredException("Token has expired")

        with patch.object(handlers.logger, "warning"):
            response = self._run_async(app_exception_handler(request, exc))

        self.assertIsInstance(response, JSONResponse)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        set_cookie_headers = response.headers.getlist("set-cookie")
        self.assertEqual(len(set_cookie_headers), 2)
        self.assertTrue(any("Max-Age=0" in header for header in set_cookie_headers))
