import logging
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from starlette.status import HTTP_200_OK, HTTP_405_METHOD_NOT_ALLOWED

from app.main import app
from app.schemas import ErrorCode
from app.schemas.auth import SessionResponseSchema, SessionMethodNotAllowedSchema
from app.services.auth.common import create_anon_token
from app.services.auth.constants import AUTH_ACCESS_COOKIE_NAME, AUTH_ANON_COOKIE_NAME


class TestAuthSessionEndpoint(TestCase):
    """Тесты для auth session endpoint."""

    def setUp(self):
        """Настройка тестового клиента."""
        logging.disable(logging.CRITICAL)

        self.client = TestClient(app)
        self.session_url = "/api/v1/auth/session"

    def test_session_none_when_no_cookies(self):
        """Если cookies нет, возвращает статус none."""
        response = self.client.get(self.session_url)
        self.assertEqual(response.status_code, HTTP_200_OK)

        data = response.json()
        schema = SessionResponseSchema(**data)
        self.assertEqual(schema.code, "OK")
        self.assertEqual(schema.status, "none")
        self.assertIsNone(schema.user_id)
        self.assertIsNone(schema.anon_id)

    def test_session_anonymous_with_anon_cookie(self):
        """Если есть валидный anon cookie, возвращает статус anonymous."""
        anon_id = uuid4()
        anon_token = create_anon_token(anon_id)
        self.client.cookies.set(AUTH_ANON_COOKIE_NAME, anon_token)

        response = self.client.get(self.session_url)
        self.assertEqual(response.status_code, HTTP_200_OK)

        data = response.json()
        schema = SessionResponseSchema(**data)
        self.assertEqual(schema.status, "anonymous")
        UUID(schema.anon_id)
        self.assertEqual(schema.anon_id, str(anon_id))

    def test_session_authenticated_with_access_cookie(self):
        """Если есть валидный access cookie, возвращает статус authenticated."""
        user_id = uuid4()
        self.client.cookies.set(AUTH_ACCESS_COOKIE_NAME, "access-token")

        with patch(
            "app.services.auth.use_cases.session.authenticate_access_token",
            new=AsyncMock(return_value=SimpleNamespace(id=user_id)),
        ):
            response = self.client.get(self.session_url)

        self.assertEqual(response.status_code, HTTP_200_OK)

        data = response.json()
        schema = SessionResponseSchema(**data)
        self.assertEqual(schema.status, "authenticated")
        self.assertEqual(schema.user_id, str(user_id))
        self.assertIsNone(schema.anon_id)

    def test_session_method_not_allowed_different_methods(self):
        """Различные HTTP методы (POST, PUT, DELETE, PATCH) возвращают 405."""
        methods = ["post", "put", "delete", "patch"]
        for method in methods:
            with self.subTest(method=method):
                client_method = getattr(self.client, method)
                response = client_method(self.session_url)
                self.assertEqual(response.status_code, HTTP_405_METHOD_NOT_ALLOWED)

                data = response.json()
                schema = SessionMethodNotAllowedSchema(**data)
                self.assertEqual(schema.code, ErrorCode.METHOD_NOT_ALLOWED)
