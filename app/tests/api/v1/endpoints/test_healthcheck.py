import logging
from unittest import TestCase
from unittest.mock import patch
from fastapi.testclient import TestClient
from starlette.status import (
    HTTP_200_OK,
    HTTP_405_METHOD_NOT_ALLOWED,
    HTTP_503_SERVICE_UNAVAILABLE,
)

from app.main import app
from app.schemas import ErrorCode
from app.schemas.healthcheck import (
    HealthcheckMethodNotAllowedSchema,
    HealthcheckResponseSchema,
    HealthcheckServiceUnavailableSchema,
)


class TestHealthcheckEndpoint(TestCase):
    """Тесты для healthcheck endpoint."""

    def setUp(self):
        """Настройка тестового клиента."""
        logging.disable(logging.CRITICAL)

        self.client = TestClient(app)
        self.healthcheck_url = "/api/v1/healthcheck"

    def test_healthcheck_success_response_schema(self):
        """Успешный healthcheck возвращает статус 200 OK и корректную схему ответа HealthcheckResponseSchema."""
        response = self.client.get(self.healthcheck_url)
        self.assertEqual(response.status_code, HTTP_200_OK)

        data = response.json()
        schema = HealthcheckResponseSchema(**data)
        self.assertEqual(schema.code, "OK")
        self.assertEqual(schema.message, "Service is available")

    def test_healthcheck_multiple_requests(self):
        """Множественные запросы к healthcheck работают корректно."""
        for _ in range(5):
            response = self.client.get(self.healthcheck_url)
            self.assertEqual(response.status_code, HTTP_200_OK)

            data = response.json()
            schema = HealthcheckResponseSchema(**data)
            self.assertEqual(schema.code, "OK")
            self.assertEqual(schema.message, "Service is available")

    def test_healthcheck_response_content_type(self):
        """Healthcheck возвращает JSON с правильным Content-Type."""
        response = self.client.get(self.healthcheck_url)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.headers["content-type"], "application/json")

    def test_healthcheck_method_not_allowed_different_methods(self):
        """Различные HTTP методы (POST, PUT, DELETE, PATCH) возвращают 405."""
        methods = ["post", "put", "delete", "patch"]
        for method in methods:
            with self.subTest(method=method):
                client_method = getattr(self.client, method)
                response = client_method(self.healthcheck_url)
                self.assertEqual(response.status_code, HTTP_405_METHOD_NOT_ALLOWED)

                data = response.json()
                schema = HealthcheckMethodNotAllowedSchema(**data)
                self.assertEqual(schema.code, ErrorCode.METHOD_NOT_ALLOWED)

    def test_healthcheck_method_not_allowed_content_type(self):
        """При ошибке 405 healthcheck возвращает JSON с правильным Content-Type."""
        response = self.client.post(self.healthcheck_url)
        self.assertEqual(response.status_code, HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.headers["content-type"], "application/json")
