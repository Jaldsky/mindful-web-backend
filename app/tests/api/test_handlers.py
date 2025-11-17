import asyncio
from unittest import TestCase
from unittest.mock import Mock
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.handlers import method_not_allowed_handler
from app.api.routes import HEALTHCHECK_PATH, SEND_EVENTS_PATH
from app.schemas import ErrorCode
from app.schemas.events import SendEventsMethodNotAllowedSchema
from app.schemas.healthcheck import HealthcheckMethodNotAllowedSchema


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
        self.assertIn("detail", data)
        detail = data["detail"]

        schema = HealthcheckMethodNotAllowedSchema(**detail)
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
        self.assertIn("detail", data)
        detail = data["detail"]

        schema = SendEventsMethodNotAllowedSchema(**detail)
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
