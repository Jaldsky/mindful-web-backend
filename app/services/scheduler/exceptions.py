from ...common.common import FormException, StringEnum
from ...db.types import ExceptionMessage


class SchedulerServiceException(FormException):
    """Базовое исключение сервиса планировщика."""


class OrchestratorTimeoutException(SchedulerServiceException):
    """Исключение при таймауте выполнения Celery задачи."""

    def __init__(self, task_id: str, message: str):
        """Инициализация исключения.

        Args:
            task_id: Идентификатор задачи.
            message: Сообщение об ошибке из OrchestratorServiceMessages.
        """
        self.task_id = task_id
        super().__init__(message)


class OrchestratorBrokerUnavailableException(SchedulerServiceException):
    """Исключение при недоступности Celery брокера."""

    def __init__(self, message: str):
        """Инициализация исключения.

        Args:
            message: Сообщение об ошибке из OrchestratorServiceMessages.
        """
        super().__init__(message)


class OrchestratorServiceMessages(StringEnum):
    """Перечисление сообщений об ошибках."""

    TASK_TIMEOUT: ExceptionMessage = "Task execution timeout for task {task_id}!"
    BROKER_UNAVAILABLE: ExceptionMessage = "Celery broker is not available!"
