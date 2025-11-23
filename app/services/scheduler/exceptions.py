from fastapi import status
from app.exceptions import AppException
from ...common.common import StringEnum
from ...db.types import ExceptionMessage


class SchedulerServiceException(AppException):
    """Базовое исключение сервиса планировщика."""


class OrchestratorTimeoutException(SchedulerServiceException):
    """Исключение при таймауте выполнения Celery задачи."""

    status_code = status.HTTP_202_ACCEPTED
    error_code = "ACCEPTED"

    def __init__(self, task_id: str, message: str):
        """Инициализация исключения.

        Args:
            task_id: Идентификатор задачи.
            message: Сообщение об ошибке из OrchestratorServiceMessages.
        """
        self.task_id = task_id
        super().__init__(message=message)

    def get_response_content(self) -> dict:
        """Метод формирования тела ответа.

        Returns:
            Тела ответа.
        """
        return {
            "code": self.error_code,
            "message": self.message,
            "task_id": self.task_id,
        }


class OrchestratorBrokerUnavailableException(SchedulerServiceException):
    """Исключение при недоступности Celery брокера."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "SERVICE_UNAVAILABLE"

    def __init__(self, message: str):
        """Инициализация исключения.

        Args:
            message: Сообщение об ошибке из OrchestratorServiceMessages.
        """
        super().__init__(message=message)


class OrchestratorServiceMessages(StringEnum):
    """Перечисление сообщений об ошибках."""

    TASK_TIMEOUT: ExceptionMessage = "Task execution timeout for task {task_id}!"
    BROKER_UNAVAILABLE: ExceptionMessage = "Celery broker is not available!"
