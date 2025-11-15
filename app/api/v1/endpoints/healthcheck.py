from fastapi import APIRouter, HTTPException
from starlette.status import (
    HTTP_200_OK,
    HTTP_405_METHOD_NOT_ALLOWED,
    HTTP_503_SERVICE_UNAVAILABLE,
)

from ....schemas import ErrorCode
from ....schemas.healthcheck import (
    HealthcheckMethodNotAllowedSchema,
    HealthcheckResponseSchema,
    HealthcheckServiceUnavailableSchema,
)

router = APIRouter(prefix="/healthcheck", tags=["healthcheck"])


@router.get(
    "",
    response_model=HealthcheckResponseSchema,
    responses={
        HTTP_200_OK: {
            "description": "Сервис работает корректно",
        },
        HTTP_405_METHOD_NOT_ALLOWED: {  # обработку см. в handlers.py
            "model": HealthcheckMethodNotAllowedSchema,
            "description": "Поддерживается только GET метод",
        },
        HTTP_503_SERVICE_UNAVAILABLE: {
            "model": HealthcheckServiceUnavailableSchema,
            "description": "Сервис не доступен",
        },
    },
    summary="Работоспособность сервиса",
    description="Проверка работоспособности сервиса",
)
async def check_service_health():
    try:
        return HealthcheckResponseSchema(
            code="OK",
            message="Service is available",
        )
    except Exception:
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail=HealthcheckServiceUnavailableSchema(
                code=ErrorCode.SERVICE_UNAVAILABLE,
                message="Service is not available",
            ).model_dump(mode="json"),
        )
