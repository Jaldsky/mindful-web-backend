from abc import ABC, abstractmethod
from celery import Celery


class CeleryConfiguratorBase(ABC):
    """Базовый класс конфигуратора Celery."""

    def __init__(self, url: str):
        """Инициализация конфигуратора.

        Args:
            url: URL для подключения к Redis (broker и backend).
        """
        self.redis_url = url

    @abstractmethod
    def exec(self) -> Celery:
        """Метод выполнения основной логики."""


class CeleryConfigurator(CeleryConfiguratorBase):
    """Класс конфигуратора Celery приложения."""

    def exec(self) -> Celery:
        """Создает и настраивает Celery приложение.

        Returns:
            Настроенное Celery приложение.
        """
        app = Celery(
            "scheduler",
            broker=self.redis_url,
            backend=self.redis_url,
            include=["app.services.scheduler"],
        )
        return app
