import logging
from unittest import TestCase
from uuid import UUID

from fastapi.testclient import TestClient
from starlette.status import (
    HTTP_201_CREATED,
    HTTP_405_METHOD_NOT_ALLOWED,
)

from app.main import app
from app.schemas import ErrorCode
from app.schemas.auth import AnonymousResponseSchema, AnonymousMethodNotAllowedSchema
from app.services.auth.common import decode_token


class TestAuthAnonymousEndpoint(TestCase):
    """Тесты для auth anonymous endpoint."""

    def setUp(self):
        """Настройка тестового клиента."""
        logging.disable(logging.CRITICAL)

        self.client = TestClient(app)
        self.anonymous_url = "/api/v1/auth/anonymous"

    def test_anonymous_success_response_schema(self):
        """Успешное создание анонимной сессии возвращает 201 и корректную схему ответа."""
        response = self.client.post(self.anonymous_url)
        self.assertEqual(response.status_code, HTTP_201_CREATED)

        data = response.json()
        schema = AnonymousResponseSchema(**data)
        self.assertEqual(schema.code, "CREATED")
        self.assertEqual(schema.message, "Anonymous session created")
        UUID(schema.anon_id)
        self.assertTrue(schema.anon_token)

        payload = decode_token(schema.anon_token)
        self.assertEqual(payload.get("type"), "anon")
        self.assertEqual(payload.get("sub"), schema.anon_id)

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
