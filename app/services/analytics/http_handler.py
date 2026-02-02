from fastapi import Request
from fastapi.responses import JSONResponse

from ...core.http_responses import method_not_allowed_response
from ...schemas.analytics import AnalyticsUsageMethodNotAllowedSchema


def analytics_usage_method_not_allowed_response(request: Request) -> JSONResponse:
    """Функция возврата ответа 405 Method Not Allowed для GET /analytics/usage.

    Returns:
        JSONResponse с ошибкой 405 Method Not Allowed.
    """
    return method_not_allowed_response(request, AnalyticsUsageMethodNotAllowedSchema, allowed_method="GET")
