from fastapi.responses import JSONResponse

from ...common.http_responses import method_not_allowed_response
from ...schemas.healthcheck import (
    HealthcheckMethodNotAllowedSchema,
    DatabaseHealthcheckMethodNotAllowedSchema,
)


def healthcheck_method_not_allowed_response() -> JSONResponse:
    """Функция возврата ответа 405 Method Not Allowed для POST /healthcheck

    Returns:
        JSONResponse с ошибкой 405 Method Not Allowed.
    """
    return method_not_allowed_response(HealthcheckMethodNotAllowedSchema, allowed_method="GET")


def database_healthcheck_method_not_allowed_response() -> JSONResponse:
    """Функция возврата ответа 405 Method Not Allowed для POST /healthcheck/database

    Returns:
        JSONResponse с ошибкой 405 Method Not Allowed.
    """
    return method_not_allowed_response(DatabaseHealthcheckMethodNotAllowedSchema, allowed_method="GET")
