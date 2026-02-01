import asyncio
import json
from unittest import TestCase
from unittest.mock import Mock, patch
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.handlers import (
    app_exception_handler,
    method_not_allowed_handler,
    bad_request_error_handler,
    unprocessable_entity_handler,
    internal_server_error_handler,
    service_unavailable_handler,
    unhandled_exception_handler,
)
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
        data = json.loads(content)
        schema = ProfileMethodNotAllowedSchema(**data)
        self.assertEqual(schema.code, ErrorCode.METHOD_NOT_ALLOWED)


def _create_mock_request(path: str = "/") -> Request:
    """Создание мок-объекта Request с указанным путём."""
    mock_request = Mock(spec=Request)
    mock_url = Mock()
    mock_url.path = path
    mock_request.url = mock_url
    return mock_request


def _run_async(coro):
    """Вспомогательная функция для запуска асинхронного кода."""
    return asyncio.run(coro)


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

    def test_non_app_exception_returns_500(self):
        """Если передано не AppException, возвращается 500 с общим сообщением."""
        request = _create_mock_request()
        exc = ValueError("internal detail")

        response = _run_async(app_exception_handler(request, exc))

        self.assertIsInstance(response, JSONResponse)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = json.loads(response.body.decode("utf-8"))
        self.assertEqual(data["code"], ErrorCode.INTERNAL_ERROR)
        self.assertEqual(data["message"], "Unknown exception type handled by app_exception_handler")
        self.assertNotIn("internal detail", data.get("message", ""))


class TestUnhandledExceptionHandler(TestCase):
    """Тесты для обработчика необработанных исключений."""

    def test_returns_500_with_generic_message(self):
        """Возвращает 500 и общее сообщение, детали исключения не уходят в ответ."""
        request = _create_mock_request()
        exc = RuntimeError("sensitive internal error")

        with patch.object(handlers.logger, "error"):
            response = _run_async(unhandled_exception_handler(request, exc))

        self.assertIsInstance(response, JSONResponse)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = json.loads(response.body.decode("utf-8"))
        self.assertEqual(data["code"], ErrorCode.INTERNAL_ERROR)
        self.assertEqual(data["message"], "Internal server error")
        self.assertNotIn("sensitive", data.get("message", ""))


class TestBadRequestErrorHandler(TestCase):
    """Тесты для обработчика 400 Bad Request."""

    def test_returns_400_with_validation_details(self):
        """При RequestValidationError возвращает 400 и детали валидации."""
        request = _create_mock_request()
        mock_exc = Mock(spec=RequestValidationError)
        mock_exc.errors.return_value = [
            {"loc": ("body", "email"), "msg": "field required", "input": None},
        ]

        with patch.object(handlers.logger, "warning"):
            response = _run_async(bad_request_error_handler(request, mock_exc))

        self.assertIsInstance(response, JSONResponse)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.body.decode("utf-8"))
        self.assertEqual(data["code"], ErrorCode.VALIDATION_ERROR)
        self.assertEqual(data["message"], "Payload validation failed")
        self.assertIsNotNone(data.get("details"))


class TestInternalServerErrorHandler(TestCase):
    """Тесты для обработчика 500 Internal Server Error."""

    def test_generic_exception_returns_generic_message(self):
        """Детали исключения не уходят на фронт — только общее сообщение."""
        request = _create_mock_request()
        exc = Exception("db connection failed: password=secret")

        with patch.object(handlers.logger, "error"):
            response = _run_async(internal_server_error_handler(request, exc))

        self.assertIsInstance(response, JSONResponse)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = json.loads(response.body.decode("utf-8"))
        self.assertEqual(data["message"], "Internal server error")
        self.assertNotIn("secret", str(data))
        self.assertNotIn("db connection failed", data.get("message", ""))

    def test_database_exception_returns_database_error_code(self):
        """При ошибке БД возвращается код DATABASE_ERROR и сообщение Database error."""
        from app.db.exceptions import DatabaseManagerException

        request = _create_mock_request()
        exc = DatabaseManagerException("session error: internal")

        with patch.object(handlers.logger, "error"):
            response = _run_async(internal_server_error_handler(request, exc))

        self.assertIsInstance(response, JSONResponse)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        data = json.loads(response.body.decode("utf-8"))
        self.assertEqual(data["code"], ErrorCode.DATABASE_ERROR)
        self.assertEqual(data["message"], "Database error")
        self.assertNotIn("internal", data.get("message", ""))


class TestServiceUnavailableHandler(TestCase):
    """Тесты для обработчика 503 Service Unavailable."""

    def test_returns_503_with_generic_message(self):
        """Возвращает 503 и общее сообщение, exc.detail не уходит в ответ."""
        request = _create_mock_request()
        exc = StarletteHTTPException(status_code=503, detail="internal reason")

        with patch.object(handlers.logger, "error"):
            response = _run_async(service_unavailable_handler(request, exc))

        self.assertIsInstance(response, JSONResponse)
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        data = json.loads(response.body.decode("utf-8"))
        self.assertEqual(data["code"], ErrorCode.SERVICE_UNAVAILABLE)
        self.assertEqual(data["message"], "Service is not available")
        self.assertNotIn("internal reason", data.get("message", ""))


class TestUnprocessableEntityHandler(TestCase):
    """Тесты для обработчика 422 Unprocessable Entity."""

    def test_string_detail_passed_to_message(self):
        """Строковый exc.detail прокидывается в message."""
        request = _create_mock_request()
        exc = StarletteHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Email already exists",
        )

        response = _run_async(unprocessable_entity_handler(request, exc))

        self.assertIsInstance(response, JSONResponse)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        data = json.loads(response.body.decode("utf-8"))
        self.assertEqual(data["code"], ErrorCode.BUSINESS_VALIDATION_ERROR)
        self.assertEqual(data["message"], "Email already exists")

    def test_dict_detail_returns_generic_message(self):
        """При exc.detail в виде dict на фронт идёт общее сообщение."""
        request = _create_mock_request()
        exc = StarletteHTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"internal": "leak"},
        )

        with patch.object(handlers.logger, "warning"):
            response = _run_async(unprocessable_entity_handler(request, exc))

        self.assertIsInstance(response, JSONResponse)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        data = json.loads(response.body.decode("utf-8"))
        self.assertEqual(data["message"], "Business validation failed")
        self.assertNotIn("internal", str(data.get("message", "")))
