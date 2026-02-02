from fastapi import Request
from fastapi.responses import JSONResponse

from ...core.http_responses import method_not_allowed_response
from ...schemas.healthcheck import (
    HealthcheckMethodNotAllowedSchema,
    DatabaseHealthcheckMethodNotAllowedSchema,
)


def healthcheck_method_not_allowed_response(request: Request) -> JSONResponse:
    """Функция возврата ответа 405 Method Not Allowed для POST /healthcheck

    Returns:
        JSONResponse с ошибкой 405 Method Not Allowed.
    """
    return method_not_allowed_response(request, HealthcheckMethodNotAllowedSchema, allowed_method="GET")


def database_healthcheck_method_not_allowed_response(request: Request) -> JSONResponse:
    """Функция возврата ответа 405 Method Not Allowed для POST /healthcheck/database

    Returns:
        JSONResponse с ошибкой 405 Method Not Allowed.
    """
    return method_not_allowed_response(request, DatabaseHealthcheckMethodNotAllowedSchema, allowed_method="GET")
