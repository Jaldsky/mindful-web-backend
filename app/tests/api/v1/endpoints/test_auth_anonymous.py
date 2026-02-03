import logging
from unittest import TestCase
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from starlette.status import (
    HTTP_201_CREATED,
    HTTP_405_METHOD_NOT_ALLOWED,
)

from app.main import app
from app.api.dependencies import get_anonymous_service
from app.schemas import ErrorCode
from app.schemas.auth import AnonymousResponseSchema, AnonymousMethodNotAllowedSchema


class TestAuthAnonymousEndpoint(TestCase):
    """Тесты для auth anonymous endpoint."""

    def setUp(self):
        """Настройка тестового клиента."""
        logging.disable(logging.CRITICAL)

        self.mock_anonymous_service = Mock()
        self.mock_anonymous_service.exec = AsyncMock(return_value=(uuid4(), "fake-anon-token"))
        app.dependency_overrides[get_anonymous_service] = lambda: self.mock_anonymous_service

        self.client = TestClient(app)
        self.anonymous_url = "/api/v1/auth/anonymous"

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_anonymous_success_response_schema(self):
        """Успешное создание анонимной сессии возвращает 201 и корректную схему ответа."""
        response = self.client.post(self.anonymous_url)
        self.assertEqual(response.status_code, HTTP_201_CREATED)

        data = response.json()
        schema = AnonymousResponseSchema(**data)
        self.assertEqual(schema.code, "CREATED")
        self.assertEqual(schema.message, "Anonymous session created")
        UUID(schema.anon_id)

    def test_anonymous_method_not_allowed_different_methods(self):
        """Различные HTTP методы (GET, PUT, DELETE, PATCH) возвращают 405."""
        methods = ["get", "put", "delete", "patch"]
        for method in methods:
            with self.subTest(method=method):
                client_method = getattr(self.client, method)
                response = client_method(self.anonymous_url)
                self.assertEqual(response.status_code, HTTP_405_METHOD_NOT_ALLOWED)

                data = response.json()
                schema = AnonymousMethodNotAllowedSchema(**data)
                self.assertEqual(schema.code, ErrorCode.METHOD_NOT_ALLOWED)

    def test_anonymous_response_content_type(self):
        """Anonymous endpoint возвращает JSON с правильным Content-Type."""
        response = self.client.post(self.anonymous_url)
        self.assertEqual(response.status_code, HTTP_201_CREATED)
        self.assertEqual(response.headers["content-type"], "application/json")
