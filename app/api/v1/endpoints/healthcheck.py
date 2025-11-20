from fastapi import APIRouter
from starlette.status import (
    HTTP_200_OK,
    HTTP_405_METHOD_NOT_ALLOWED,
    HTTP_503_SERVICE_UNAVAILABLE,
)

from ....schemas.general import ServiceUnavailableSchema
from ....schemas.healthcheck import (
    HealthcheckMethodNotAllowedSchema,
    HealthcheckResponseSchema,
)

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
        HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ServiceUnavailableSchema,
            "description": "Сервис не доступен",
        },
    },
    summary="Работоспособность сервиса",
    description="Проверка работоспособности сервиса",
)
async def check_service_health():
    return HealthcheckResponseSchema(
        code="OK",
        message="Service is available",
    )
