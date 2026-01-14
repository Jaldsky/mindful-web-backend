from fastapi.responses import JSONResponse

from ...common.http_responses import method_not_allowed_response
from ...schemas.analytics import AnalyticsUsageMethodNotAllowedSchema


def analytics_usage_method_not_allowed_response() -> JSONResponse:
    """Функция возврата ответа 405 Method Not Allowed для GET /analytics/usage.

    Returns:
        JSONResponse с ошибкой 405 Method Not Allowed.
    """
    return method_not_allowed_response(AnalyticsUsageMethodNotAllowedSchema, allowed_method="GET")
