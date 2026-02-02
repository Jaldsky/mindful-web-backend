from fastapi.responses import JSONResponse

from ...core.http_responses import method_not_allowed_response
from ...schemas.user import (
    ProfileMethodNotAllowedSchema,
    UpdateUsernameMethodNotAllowedSchema,
    UpdateEmailMethodNotAllowedSchema,
)


def user_profile_method_not_allowed_response() -> JSONResponse:
    """Функция возврата ответа 405 Method Not Allowed для GET /user/profile.

    Returns:
        JSONResponse с ошибкой 405 Method Not Allowed.
    """
    return method_not_allowed_response(ProfileMethodNotAllowedSchema, allowed_method="GET")


def user_profile_username_method_not_allowed_response() -> JSONResponse:
    """Функция возврата ответа 405 Method Not Allowed для PATCH /user/profile/username.

    Returns:
        JSONResponse с ошибкой 405 Method Not Allowed.
    """
    return method_not_allowed_response(UpdateUsernameMethodNotAllowedSchema, allowed_method="PATCH")


def user_profile_email_method_not_allowed_response() -> JSONResponse:
    """Функция возврата ответа 405 Method Not Allowed для PATCH /user/profile/email.

    Returns:
        JSONResponse с ошибкой 405 Method Not Allowed.
    """
    return method_not_allowed_response(UpdateEmailMethodNotAllowedSchema, allowed_method="PATCH")
