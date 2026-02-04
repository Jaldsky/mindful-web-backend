from fastapi import status
from app.exceptions import AppException


class SchedulerServiceException(AppException):
    """Базовое исключение сервиса планировщика."""


class OrchestratorTimeoutException(SchedulerServiceException):
    """Исключение при таймауте выполнения Celery задачи."""

    status_code = status.HTTP_202_ACCEPTED
    error_code = "ACCEPTED"

    def __init__(self, task_id: str):
        """Инициализация исключения.

        Args:
            task_id: Идентификатор задачи.
        """
        self.task_id = task_id
        super().__init__(
            key="analytics.messages.task_timeout",
            translation_params={"task_id": task_id},
            fallback=f"Task execution timeout for task {task_id}!",
        )

    def get_response_content(self) -> dict:
        """Метод формирования тела ответа.

        Returns:
            Тела ответа.
        """
        return {
            "code": self.error_code,
            "message": self.fallback,
            "task_id": self.task_id,
        }


class OrchestratorBrokerUnavailableException(SchedulerServiceException):
    """Исключение при недоступности Celery брокера."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "SERVICE_UNAVAILABLE"
