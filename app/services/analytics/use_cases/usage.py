from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from ..types import Page, Date
from ....schemas.analytics import AnalyticsUsageResponseOkSchema


@dataclass(slots=True, frozen=True)
class AnalyticsUsage:
    """Входные данные для получения аналитики использования по доменам."""

    user_id: UUID
    from_date: Date
    to_date: Date
    page: Page = 1


class AnalyticsUsageServiceBase:
    """Базовый класс сервиса analytics usage."""

    _data: AnalyticsUsage

    def __init__(self, **kwargs: Any) -> None:
        """Инициализация сервиса.

        Args:
            **kwargs: Аргументы для AnalyticsUsage.
        """
        self._data = AnalyticsUsage(**kwargs)

    @property
    def user_id(self) -> UUID:
        """Свойство получения user_id из входных данных.

        Returns:
            Идентификатор пользователя.
        """
        return self._data.user_id

    @property
    def from_date(self) -> Date:
        """Свойство получения from_date из входных данных.

        Returns:
            Дата начала периода.
        """
        return self._data.from_date

    @property
    def to_date(self) -> Date:
        """Свойство получения to_date из входных данных.

        Returns:
            Дата окончания периода.
        """
        return self._data.to_date

    @property
    def page(self) -> Page:
        """Свойство получения page из входных данных.

        Returns:
            Страница.
        """
        return self._data.page


class AnalyticsUsageService(AnalyticsUsageServiceBase):
    """Сервис получения статистики активности пользователя по доменам."""

    async def exec(self) -> AnalyticsUsageResponseOkSchema:
        """Метод получения статистики использования по доменам.

        Процесс включает:
        1. Постановку задачи вычисления в очередь
        2. Ожидание результата в рамках таймаута orchestrator
        3. Приведение результата к схеме ответа

        Returns:
            Схема ответа AnalyticsUsageResponseOkSchema.

        Raises:
            OrchestratorTimeoutException: Если задача не успела выполниться в пределах таймаута (202).
            OrchestratorBrokerUnavailableException: Если брокер Celery недоступен (503).
        """
        # Ленивая загрузка, чтобы импорт app.services.analytics не требовал Celery сразу.
        from ...scheduler import Orchestrator, compute_domain_usage_task

        orchestrator = Orchestrator()
        data_dict: dict[str, Any] = orchestrator.exec(
            task=compute_domain_usage_task,
            user_id=self.user_id,
            start_date=self.from_date,
            end_date=self.to_date,
            page=self.page,
        )
        return AnalyticsUsageResponseOkSchema(**data_dict)
