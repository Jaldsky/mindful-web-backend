from fastapi.responses import JSONResponse

from ...common.http_responses import method_not_allowed_response
from ...schemas.user import UserProfileMethodNotAllowedSchema


def user_profile_method_not_allowed_response() -> JSONResponse:
    """Функция возврата ответа 405 Method Not Allowed для GET /user/profile.

    Returns:
        JSONResponse с ошибкой 405 Method Not Allowed.
    """
    return method_not_allowed_response(UserProfileMethodNotAllowedSchema, allowed_method="GET")
