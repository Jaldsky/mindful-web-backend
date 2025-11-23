from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from starlette import status

from ...dependencies import get_user_id_from_header
from ....schemas.analytics import (
    AnalyticsUsageRequestSchema,
    AnalyticsUsageResponseAcceptedSchema,
    AnalyticsUsageResponseOkSchema,
)
from ....services.scheduler import Orchestrator, compute_domain_usage_task

router = APIRouter(prefix="/analytics", tags=["analytics"])


def validate_usage_request_params(
    from_date: Annotated[
        str,
        Query(alias="from", description="Начало интервала (дата в формате DD-MM-YYYY)", example="05-04-2025"),
    ],
    to_date: Annotated[
        str,
        Query(alias="to", description="Конец интервала (дата в формате DD-MM-YYYY)", example="05-04-2025"),
    ],
    page: Annotated[int, Query(ge=1, description="Номер страницы", example=1)] = 1,
) -> AnalyticsUsageRequestSchema:
    """Dependency для валидации параметров запроса analytics usage через Pydantic схему."""
    return AnalyticsUsageRequestSchema(
        from_date=from_date,
        to_date=to_date,
        page=page,
    )


@router.get(
    "/usage",
    responses={
        status.HTTP_200_OK: {
            "model": AnalyticsUsageResponseOkSchema,
            "description": "Готовая статистика активности по доменам",
        },
        status.HTTP_202_ACCEPTED: {
            "model": AnalyticsUsageResponseAcceptedSchema,
            "description": "Задача поставлена в очередь, результат будет готов позже",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Ошибка валидации параметров запроса",
        },
    },
    summary="Статистика активности пользователя по доменам",
    description=(
        "Возвращает агрегированную статистику времени активности по доменам за заданный интервал времени. "
        "Запускается через Celery задачу. По умолчанию возвращает по 20 записей на страницу."
    ),
)
async def get_domain_usage(
    request: Request,
    user_id: UUID = Depends(get_user_id_from_header),
    request_params: AnalyticsUsageRequestSchema = Depends(validate_usage_request_params),
) -> AnalyticsUsageResponseOkSchema:
    """Эндпоинт для получения статистики использования доменов.

    Args:
        user_id: Идентификатор пользователя из заголовка X-User-ID.
        request_params: Валидированные параметры запроса.

    Returns:
        AnalyticsUsageResponseOkSchema: Результаты аналитики или исключение для обработки в хендлерах.

    Raises:
        OrchestratorTimeoutException: При таймауте выполнения задачи (обрабатывается в хендлере как 202).
        OrchestratorBrokerUnavailableException: При недоступности брокера (обрабатывается в хендлере как 503).
    """

    def normalize_pagination(data: dict) -> dict:
        """Нормализует структуру пагинации в результате."""
        if "pagination" in data:
            pagination = data["pagination"]
            if "per_page" not in pagination:
                pagination["per_page"] = 20  # Значение по умолчанию
            if "next" not in pagination:
                page_num = pagination.get("page", 1)
                total_pages = pagination.get("total_pages", 0)
                pagination["next"] = page_num + 1 if page_num < total_pages else None
            if "prev" not in pagination:
                page_num = pagination.get("page", 1)
                pagination["prev"] = page_num - 1 if page_num > 1 else None
        return data

    orchestrator = Orchestrator()
    data_dict = orchestrator.exec(
        task=compute_domain_usage_task,
        user_id=str(user_id),
        start_date=request_params.from_date,
        end_date=request_params.to_date,
        page=request_params.page,
        result_processor=normalize_pagination,
    )
    data = AnalyticsUsageResponseOkSchema(**data_dict)

    def get_param_value(name: str, fallback: str) -> str:
        return request.query_params.get(name) or fallback

    from_str = get_param_value("from", request_params.from_date.strftime("%d-%m-%Y"))
    to_str = get_param_value("to", request_params.to_date.strftime("%d-%m-%Y"))

    base_url = request.url_for("get_domain_usage")

    def build_url(p: int | None) -> str | None:
        if not p:
            return None
        return f"{base_url}?from={from_str}&to={to_str}&page={p}"

    next_num = data.pagination.page + 1 if data.pagination.page < data.pagination.total_pages else None
    prev_num = data.pagination.page - 1 if data.pagination.page > 1 else None
    data.pagination.next = build_url(next_num)
    data.pagination.prev = build_url(prev_num)
    return data
