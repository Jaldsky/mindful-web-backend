from fastapi.responses import JSONResponse

from ...core.http_responses import method_not_allowed_response
from ...schemas.events import SaveEventsMethodNotAllowedSchema


def save_events_method_not_allowed_response() -> JSONResponse:
    """Функция возврата ответа 405 Method Not Allowed для POST /events/save.

    Returns:
        JSONResponse с ошибкой 405 Method Not Allowed.
    """
    return method_not_allowed_response(SaveEventsMethodNotAllowedSchema, allowed_method="POST")
