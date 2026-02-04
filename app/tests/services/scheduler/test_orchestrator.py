from unittest import TestCase
from unittest.mock import Mock, MagicMock, patch
from celery.exceptions import TimeoutError
from kombu.exceptions import OperationalError

from app.services.scheduler.orchestrator import Orchestrator
from app.services.scheduler.exceptions import (
    OrchestratorTimeoutException,
    OrchestratorBrokerUnavailableException,
)


class TestOrchestrator(TestCase):
    """Тесты для Orchestrator."""

    def setUp(self):
        """Настройка тестовых данных."""
        self.task_timeout = 3
        self.orchestrator = Orchestrator(task_timeout=self.task_timeout)
        self.mock_task = Mock()
        self.mock_task.name = "test_task"

    @patch("app.services.scheduler.orchestrator.logger")
    def test_exec_success(self, mock_logger):
        """Успешное выполнение задачи."""
        mock_celery_task = MagicMock()
        mock_celery_task.id = "task-123"
        mock_celery_task.get.return_value = {"result": "success"}
        self.mock_task.delay.return_value = mock_celery_task

        result = self.orchestrator.exec(self.mock_task, "arg1", "arg2", kwarg1="value1")

        self.assertEqual(result, {"result": "success"})
        self.mock_task.delay.assert_called_once_with("arg1", "arg2", kwarg1="value1")
        mock_celery_task.get.assert_called_once_with(timeout=self.task_timeout)

    @patch("app.services.scheduler.orchestrator.logger")
    def test_exec_with_result_processor(self, _):
        """Выполнение задачи с обработчиком результата."""
        mock_celery_task = MagicMock()
        mock_celery_task.id = "task-123"
        mock_celery_task.get.return_value = {"data": "raw"}
        self.mock_task.delay.return_value = mock_celery_task

        def processor(data):
            return {"processed": data["data"]}

        result = self.orchestrator.exec(self.mock_task, result_processor=processor, arg1="value1")

        self.assertEqual(result, {"processed": "raw"})
        mock_celery_task.get.assert_called_once_with(timeout=self.task_timeout)

    @patch("app.services.scheduler.orchestrator.logger")
    def test_exec_timeout_error(self, mock_logger):
        """Обработка таймаута выполнения задачи."""
        mock_celery_task = MagicMock()
        mock_celery_task.id = "task-123"
        mock_celery_task.get.side_effect = TimeoutError("Task timeout")
        self.mock_task.delay.return_value = mock_celery_task

        with self.assertRaises(OrchestratorTimeoutException) as cm:
            self.orchestrator.exec(self.mock_task)

        self.assertEqual(cm.exception.task_id, "task-123")
        self.assertEqual(
            cm.exception.message,
            "Task execution timeout for task task-123!",
        )
        mock_logger.warning.assert_called_once_with("Celery task timeout for task test_task")

    @patch("app.services.scheduler.orchestrator.logger")
    def test_exec_timeout_error_no_task_id(self, mock_logger):
        """Обработка таймаута когда celery_task не создан."""
        self.mock_task.delay.side_effect = TimeoutError("Task timeout")

        with self.assertRaises(OrchestratorTimeoutException) as cm:
            self.orchestrator.exec(self.mock_task)

        self.assertEqual(cm.exception.task_id, "unknown")
        self.assertEqual(
            cm.exception.message,
            "Task execution timeout for task unknown!",
        )
        mock_logger.warning.assert_called_once_with("Celery task timeout for task test_task")

    @patch("app.services.scheduler.orchestrator.logger")
    def test_exec_operational_error(self, mock_logger):
        """Обработка ошибки недоступности брокера."""
        self.mock_task.delay.side_effect = OperationalError("Broker unavailable")

        with self.assertRaises(OrchestratorBrokerUnavailableException) as cm:
            self.orchestrator.exec(self.mock_task)

        self.assertEqual(cm.exception.message_key, "scheduler.errors.broker_unavailable")

    @patch("app.services.scheduler.orchestrator.logger")
    def test_exec_task_without_name(self, _):
        """Обработка задачи без атрибута name."""
        mock_celery_task = MagicMock()
        mock_celery_task.id = "task-123"
        mock_celery_task.get.return_value = {"result": "success"}
        self.mock_task.delay.return_value = mock_celery_task
        del self.mock_task.name

        result = self.orchestrator.exec(self.mock_task)

        self.assertEqual(result, {"result": "success"})
        mock_celery_task.get.assert_called_once_with(timeout=self.task_timeout)

    def test_init_default_timeout(self):
        """Инициализация с дефолтным таймаутом."""
        orchestrator = Orchestrator()
        self.assertEqual(orchestrator.task_timeout, 3)

    def test_init_custom_timeout(self):
        """Инициализация с кастомным таймаутом."""
        custom_timeout = 10
        orchestrator = Orchestrator(task_timeout=custom_timeout)
        self.assertEqual(orchestrator.task_timeout, custom_timeout)

    @patch("app.services.scheduler.orchestrator.logger")
    def test_exec_with_args_and_kwargs(self, _):
        """Выполнение задачи с позиционными и именованными аргументами."""
        mock_celery_task = MagicMock()
        mock_celery_task.id = "task-123"
        mock_celery_task.get.return_value = {"result": "success"}
        self.mock_task.delay.return_value = mock_celery_task

        result = self.orchestrator.exec(self.mock_task, "pos_arg1", "pos_arg2", kwarg1="value1", kwarg2="value2")

        self.assertEqual(result, {"result": "success"})
        self.mock_task.delay.assert_called_once_with("pos_arg1", "pos_arg2", kwarg1="value1", kwarg2="value2")

    @patch("app.services.scheduler.orchestrator.logger")
    def test_exec_result_processor_modifies_data(self, _):
        """Обработчик результата корректно модифицирует данные."""
        mock_celery_task = MagicMock()
        mock_celery_task.id = "task-123"
        mock_celery_task.get.return_value = [1, 2, 3]
        self.mock_task.delay.return_value = mock_celery_task

        def processor(data):
            return {"count": len(data), "sum": sum(data)}

        result = self.orchestrator.exec(self.mock_task, result_processor=processor)

        self.assertEqual(result, {"count": 3, "sum": 6})
