from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import (
    HTTP_200_OK,
    HTTP_405_METHOD_NOT_ALLOWED,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_503_SERVICE_UNAVAILABLE,
)

from ....core.localizer import localize_key
from ...dependencies import get_db_session
from ....schemas.general import (
    InternalServerErrorSchema,
    ServiceUnavailableSchema,
)
from ....schemas.healthcheck import (
    HealthcheckMethodNotAllowedSchema,
    HealthcheckResponseSchema,
    DatabaseHealthcheckResponseSchema,
    DatabaseHealthcheckMethodNotAllowedSchema,
    DatabaseHealthcheckInternalServerErrorSchema,
    DatabaseHealthcheckServiceUnavailableSchema,
)
from ....services.healthcheck import DatabaseHealthcheckService

router = APIRouter(prefix="/healthcheck", tags=["healthcheck"])


@router.get(
    "",
    response_model=HealthcheckResponseSchema,
    responses={
        HTTP_200_OK: {
            "description": "Сервис работает корректно",
        },
        HTTP_405_METHOD_NOT_ALLOWED: {
            "model": HealthcheckMethodNotAllowedSchema,
            "description": "Поддерживается только GET метод",
        },
        HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": InternalServerErrorSchema,
            "description": "Внутренняя ошибка сервера",
        },
        HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ServiceUnavailableSchema,
            "description": "Сервис не доступен",
        },
    },
    summary="Проверка доступности сервиса",
    description="Проверка работоспособности сервиса",
)
async def check_service_health(request: Request) -> HealthcheckResponseSchema:
    message = localize_key(request, "healthcheck.messages.service_available", "Service is available")
    return HealthcheckResponseSchema(code="OK", message=message)


@router.get(
    "/database",
    response_model=DatabaseHealthcheckResponseSchema,
    responses={
        HTTP_200_OK: {
            "description": "База данных доступна",
        },
        HTTP_405_METHOD_NOT_ALLOWED: {
            "model": DatabaseHealthcheckMethodNotAllowedSchema,
            "description": "Поддерживается только GET метод",
        },
        HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": DatabaseHealthcheckInternalServerErrorSchema,
            "description": "Внутренняя ошибка сервера",
        },
        HTTP_503_SERVICE_UNAVAILABLE: {
            "model": DatabaseHealthcheckServiceUnavailableSchema,
            "description": "База данных недоступна",
        },
    },
    summary="Проверка доступности базы данных",
    description="Проверяет подключение к базе данных и ее работоспособность",
)
async def check_database_health(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> DatabaseHealthcheckResponseSchema:
    await DatabaseHealthcheckService(session=db).exec()

    message = localize_key(request, "healthcheck.messages.database_available", "Database is available")
    return DatabaseHealthcheckResponseSchema(code="OK", message=message)
