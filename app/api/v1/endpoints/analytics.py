from fastapi import APIRouter, Depends, Request
from starlette import status

from ...dependencies import validate_usage_request_params, get_actor_id_from_token, ActorContext
from ....core.pagination import PaginationUrlBuilder
from ....schemas.analytics import (
    AnalyticsUsageRequestSchema,
    AnalyticsUsageResponseAcceptedSchema,
    AnalyticsUsageResponseOkSchema,
    AnalyticsUsageUnprocessableEntitySchema,
    AnalyticsUsageInternalServerErrorSchema,
    AnalyticsUsageMethodNotAllowedSchema,
)
from ....schemas.general import ServiceUnavailableSchema
from ....services.analytics import AnalyticsUsageService

router = APIRouter(prefix="/analytics", tags=["analytics"])


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
        status.HTTP_405_METHOD_NOT_ALLOWED: {
            "model": AnalyticsUsageMethodNotAllowedSchema,
            "description": "Метод не поддерживается",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": AnalyticsUsageUnprocessableEntitySchema,
            "description": "Ошибка бизнес валидации параметров запроса",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": AnalyticsUsageInternalServerErrorSchema,
            "description": "Внутренняя ошибка сервера",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ServiceUnavailableSchema,
            "description": "Сервис не доступен",
        },
    },
    summary="Статистика активности пользователя по доменам",
    description=(
        "Возвращает агрегированную статистику времени активности по доменам "
        "за заданный интервал времени. Требуется Authorization: Bearer <access token>."
    ),
)
async def get_usage(
    request: Request,
    actor: ActorContext = Depends(get_actor_id_from_token),
    request_params: AnalyticsUsageRequestSchema = Depends(validate_usage_request_params),
) -> AnalyticsUsageResponseOkSchema:
    """Эндпоинт для получения статистики использования доменов.

    Args:
        request: Объект запроса FastAPI.
        actor: Контекст пользователя или анонимной сессии из JWT.
        request_params: Валидированные параметры запроса.

    Returns:
        AnalyticsUsageResponseOkSchema: Результаты аналитики или исключение для обработки в хендлерах.

    Raises:
        OrchestratorTimeoutException: При таймауте выполнения задачи (обрабатывается в хендлере как 202).
        OrchestratorBrokerUnavailableException: При недоступности брокера (обрабатывается в хендлере как 503).
    """
    response = await AnalyticsUsageService(
        user_id=actor.actor_id,
        from_date=request_params.from_date,
        to_date=request_params.to_date,
        page=request_params.page,
    ).exec()
    response.pagination = PaginationUrlBuilder.build_links(request, response.pagination)

    return response
