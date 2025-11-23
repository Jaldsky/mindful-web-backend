import logging
from abc import ABC, abstractmethod
from typing import Any, Callable

from celery.exceptions import TimeoutError
from kombu.exceptions import OperationalError

from .exceptions import (
    OrchestratorTimeoutException,
    OrchestratorBrokerUnavailableException,
    OrchestratorServiceMessages,
)

logger = logging.getLogger(__name__)


class OrchestratorBase(ABC):
    """Базовый класс оркестратора для выполнения Celery задач."""

    messages = OrchestratorServiceMessages

    def __init__(self, task_timeout: int = 3) -> None:
        """Инициализация оркестратора.

        Args:
            task_timeout: Таймаут ожидания результата задачи в секундах.
        """
        self.task_timeout = task_timeout

    @abstractmethod
    def exec(self, *args, **kwargs):
        """Метод выполнения основной логики."""


class Orchestrator(OrchestratorBase):
    """Универсальный оркестратор для выполнения Celery задач."""

    def exec(
        self,
        task: Any,
        *args,
        result_processor: Callable[[Any], Any] | None = None,
        **kwargs,
    ) -> Any:
        """Выполняет Celery задачу с обработкой ошибок.

        Args:
            task: Celery задача для выполнения (декорированная функция с методом delay).
            *args: Позиционные аргументы для задачи.
            result_processor: Опциональная функция для постобработки результата.
            **kwargs: Именованные аргументы для задачи.

        Returns:
            Результат выполнения задачи.

        Raises:
            OrchestratorTimeoutException: При таймауте выполнения задачи.
            OrchestratorBrokerUnavailableException: При недоступности брокера.
        """
        celery_task = None
        task_name = getattr(task, "name", "unknown")
        try:
            celery_task = task.delay(*args, **kwargs)
            data = celery_task.get(timeout=self.task_timeout)

            if result_processor:
                data = result_processor(data)
            return data
        except TimeoutError:
            logger.warning(f"Celery task timeout for task {task_name}")
            task_id = celery_task.id if celery_task else "unknown"
            raise OrchestratorTimeoutException(
                task_id=task_id,
                message=self.messages.TASK_TIMEOUT.format(task_id=task_id),
            )
        except OperationalError:
            logger.error(f"Celery broker unavailable for task {task_name}")
            raise OrchestratorBrokerUnavailableException(message=self.messages.BROKER_UNAVAILABLE)
