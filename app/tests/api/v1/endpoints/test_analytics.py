import logging
from unittest import TestCase
from unittest.mock import patch, Mock
from uuid import uuid4
from fastapi.testclient import TestClient
from starlette.status import (
    HTTP_200_OK,
    HTTP_202_ACCEPTED,
    HTTP_400_BAD_REQUEST,
    HTTP_405_METHOD_NOT_ALLOWED,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_503_SERVICE_UNAVAILABLE,
)

from app.main import app
from app.schemas import ErrorCode
from app.schemas.analytics import (
    AnalyticsUsageResponseOkSchema,
    AnalyticsUsageResponseAcceptedSchema,
    AnalyticsUsageMethodNotAllowedSchema,
    AnalyticsUsageUnprocessableEntitySchema,
    AnalyticsUsageInternalServerErrorSchema,
)
from app.schemas.general import ServiceUnavailableSchema
from app.services.scheduler.exceptions import (
    OrchestratorTimeoutException,
    OrchestratorBrokerUnavailableException,
    OrchestratorServiceMessages,
)


class TestAnalyticsUsageEndpoint(TestCase):
    """Тесты для analytics usage endpoint."""

    def setUp(self):
        """Настройка тестового клиента."""
        logging.disable(logging.CRITICAL)

        self.client = TestClient(app)
        self.usage_url = "/api/v1/analytics/usage"
        self.user_id = uuid4()
        self.valid_params = {
            "from": "05-04-2025",
            "to": "05-04-2025",
            "page": 1,
        }

    def test_usage_success_response_schema(self):
        """Успешный запрос возвращает статус 200 OK и корректную схему ответа."""
        mock_data = {
            "code": "OK",
            "message": "Usage analytics computed",
            "from_date": "2025-04-05",
            "to_date": "2025-04-05",
            "pagination": {
                "page": 1,
                "per_page": 50,
                "total_items": 2,
                "total_pages": 1,
                "next": None,
                "prev": None,
            },
            "data": [
                {"domain": "docs.google.com", "category": "work", "total_seconds": 2100},
                {"domain": "youtube.com", "category": "entertainment", "total_seconds": 600},
            ],
        }

        with patch("app.api.v1.endpoints.analytics.Orchestrator") as mock_orchestrator:
            mock_orchestrator_instance = Mock()
            mock_orchestrator_instance.exec.return_value = mock_data
            mock_orchestrator.return_value = mock_orchestrator_instance

            response = self.client.get(
                self.usage_url,
                params=self.valid_params,
                headers={"X-User-ID": str(self.user_id)},
            )

            self.assertEqual(response.status_code, HTTP_200_OK)
            data = response.json()
            schema = AnalyticsUsageResponseOkSchema(**data)
            self.assertEqual(schema.code, "OK")
            self.assertEqual(schema.message, "Usage analytics computed")
            self.assertEqual(len(schema.data), 2)

    def test_usage_timeout_exception(self):
        """Таймаут выполнения задачи возвращает статус 202 ACCEPTED."""
        task_id = "test-task-id-123"
        with patch("app.api.v1.endpoints.analytics.Orchestrator") as mock_orchestrator:
            mock_orchestrator_instance = Mock()
            mock_orchestrator_instance.exec.side_effect = OrchestratorTimeoutException(
                task_id=task_id,
                message=OrchestratorServiceMessages.TASK_TIMEOUT.format(task_id=task_id),
            )
            mock_orchestrator.return_value = mock_orchestrator_instance

            response = self.client.get(
                self.usage_url,
                params=self.valid_params,
                headers={"X-User-ID": str(self.user_id)},
            )

            self.assertEqual(response.status_code, HTTP_202_ACCEPTED)
            data = response.json()
            schema = AnalyticsUsageResponseAcceptedSchema(**data)
            self.assertEqual(schema.code, "ACCEPTED")
            self.assertEqual(schema.task_id, task_id)

    def test_usage_broker_unavailable_exception(self):
        """Недоступность брокера возвращает статус 503 SERVICE_UNAVAILABLE."""
        with patch("app.api.v1.endpoints.analytics.Orchestrator") as mock_orchestrator:
            mock_orchestrator_instance = Mock()
            mock_orchestrator_instance.exec.side_effect = OrchestratorBrokerUnavailableException(
                message=OrchestratorServiceMessages.BROKER_UNAVAILABLE
            )
            mock_orchestrator.return_value = mock_orchestrator_instance

            response = self.client.get(
                self.usage_url,
                params=self.valid_params,
                headers={"X-User-ID": str(self.user_id)},
            )

            self.assertEqual(response.status_code, HTTP_503_SERVICE_UNAVAILABLE)
            data = response.json()
            schema = ServiceUnavailableSchema(**data)
            self.assertEqual(schema.code, ErrorCode.SERVICE_UNAVAILABLE)

    def test_usage_method_not_allowed_different_methods(self):
        """Различные HTTP методы (POST, PUT, DELETE, PATCH) возвращают 405."""
        methods = ["post", "put", "delete", "patch"]
        for method in methods:
            with self.subTest(method=method):
                client_method = getattr(self.client, method)
                response = client_method(
                    self.usage_url,
                    params=self.valid_params,
                    headers={"X-User-ID": str(self.user_id)},
                )
                self.assertEqual(response.status_code, HTTP_405_METHOD_NOT_ALLOWED)

                data = response.json()
                schema = AnalyticsUsageMethodNotAllowedSchema(**data)
                self.assertEqual(schema.code, ErrorCode.METHOD_NOT_ALLOWED)

    def test_usage_method_not_allowed_content_type(self):
        """При ошибке 405 возвращается JSON с правильным Content-Type."""
        response = self.client.post(
            self.usage_url,
            params=self.valid_params,
            headers={"X-User-ID": str(self.user_id)},
        )
        self.assertEqual(response.status_code, HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.headers["content-type"], "application/json")

    def test_usage_missing_required_params(self):
        """Отсутствие обязательных параметров возвращает 400."""
        # Отсутствует параметр 'from'
        response = self.client.get(
            self.usage_url,
            params={"to": "05-04-2025", "page": 1},
            headers={"X-User-ID": str(self.user_id)},
        )
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

        # Отсутствует параметр 'to'
        response = self.client.get(
            self.usage_url,
            params={"from": "05-04-2025", "page": 1},
            headers={"X-User-ID": str(self.user_id)},
        )
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_usage_invalid_date_format(self):
        """Неверный формат даты возвращает 422."""
        response = self.client.get(
            self.usage_url,
            params={"from": "invalid-date", "to": "05-04-2025", "page": 1},
            headers={"X-User-ID": str(self.user_id)},
        )
        self.assertEqual(response.status_code, HTTP_422_UNPROCESSABLE_ENTITY)

        data = response.json()
        schema = AnalyticsUsageUnprocessableEntitySchema(**data)
        self.assertIsNotNone(schema.details)

    def test_usage_invalid_page_parameter(self):
        """Неверный параметр page (меньше 1) возвращает 400."""
        response = self.client.get(
            self.usage_url,
            params={"from": "05-04-2025", "to": "05-04-2025", "page": 0},
            headers={"X-User-ID": str(self.user_id)},
        )
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_usage_invalid_user_id_format(self):
        """Неверный формат User ID возвращает 422."""
        response = self.client.get(
            self.usage_url,
            params=self.valid_params,
            headers={"X-User-ID": "invalid-uuid"},
        )
        self.assertEqual(response.status_code, HTTP_422_UNPROCESSABLE_ENTITY)

    def test_usage_without_user_id_header(self):
        """Запрос без заголовка X-User-ID генерирует новый UUID и обрабатывается успешно."""
        mock_data = {
            "code": "OK",
            "message": "Usage analytics computed",
            "from_date": "2025-04-05",
            "to_date": "2025-04-05",
            "pagination": {
                "page": 1,
                "per_page": 50,
                "total_items": 0,
                "total_pages": 0,
                "next": None,
                "prev": None,
            },
            "data": [],
        }

        with patch("app.api.v1.endpoints.analytics.Orchestrator") as mock_orchestrator:
            mock_orchestrator_instance = Mock()
            mock_orchestrator_instance.exec.return_value = mock_data
            mock_orchestrator.return_value = mock_orchestrator_instance

            response = self.client.get(
                self.usage_url,
                params=self.valid_params,
            )

            # Должен успешно обработаться с автоматически сгенерированным UUID
            self.assertEqual(response.status_code, HTTP_200_OK)
            # Проверяем, что orchestrator был вызван с каким-то user_id
            mock_orchestrator_instance.exec.assert_called_once()
            call_kwargs = mock_orchestrator_instance.exec.call_args[1]
            self.assertIn("user_id", call_kwargs)

    def test_usage_pagination_links(self):
        """Проверка корректного построения ссылок пагинации."""
        mock_data = {
            "code": "OK",
            "message": "Usage analytics computed",
            "from_date": "2025-04-05",
            "to_date": "2025-04-05",
            "pagination": {
                "page": 1,
                "per_page": 50,
                "total_items": 100,
                "total_pages": 2,
                "next": None,
                "prev": None,
            },
            "data": [],
        }

        with patch("app.api.v1.endpoints.analytics.Orchestrator") as mock_orchestrator:
            mock_orchestrator_instance = Mock()
            mock_orchestrator_instance.exec.return_value = mock_data
            mock_orchestrator.return_value = mock_orchestrator_instance

            response = self.client.get(
                self.usage_url,
                params=self.valid_params,
                headers={"X-User-ID": str(self.user_id)},
            )

            self.assertEqual(response.status_code, HTTP_200_OK)
            data = response.json()
            schema = AnalyticsUsageResponseOkSchema(**data)
            # Проверяем, что ссылки пагинации были построены
            # На первой странице должна быть ссылка на следующую
            self.assertIsNotNone(schema.pagination.next)
            self.assertIsNone(schema.pagination.prev)

    def test_usage_response_content_type(self):
        """Успешный ответ возвращает JSON с правильным Content-Type."""
        mock_data = {
            "code": "OK",
            "message": "Usage analytics computed",
            "from_date": "2025-04-05",
            "to_date": "2025-04-05",
            "pagination": {
                "page": 1,
                "per_page": 50,
                "total_items": 0,
                "total_pages": 0,
                "next": None,
                "prev": None,
            },
            "data": [],
        }

        with patch("app.api.v1.endpoints.analytics.Orchestrator") as mock_orchestrator:
            mock_orchestrator_instance = Mock()
            mock_orchestrator_instance.exec.return_value = mock_data
            mock_orchestrator.return_value = mock_orchestrator_instance

            response = self.client.get(
                self.usage_url,
                params=self.valid_params,
                headers={"X-User-ID": str(self.user_id)},
            )

            self.assertEqual(response.status_code, HTTP_200_OK)
            self.assertEqual(response.headers["content-type"], "application/json")

    def test_usage_multiple_requests(self):
        """Множественные запросы работают корректно."""
        mock_data = {
            "code": "OK",
            "message": "Usage analytics computed",
            "from_date": "2025-04-05",
            "to_date": "2025-04-05",
            "pagination": {
                "page": 1,
                "per_page": 50,
                "total_items": 0,
                "total_pages": 0,
                "next": None,
                "prev": None,
            },
            "data": [],
        }

        with patch("app.api.v1.endpoints.analytics.Orchestrator") as mock_orchestrator:
            mock_orchestrator_instance = Mock()
            mock_orchestrator_instance.exec.return_value = mock_data
            mock_orchestrator.return_value = mock_orchestrator_instance

            for _ in range(5):
                response = self.client.get(
                    self.usage_url,
                    params=self.valid_params,
                    headers={"X-User-ID": str(self.user_id)},
                )
                self.assertEqual(response.status_code, HTTP_200_OK)

                data = response.json()
                schema = AnalyticsUsageResponseOkSchema(**data)
                self.assertEqual(schema.code, "OK")
