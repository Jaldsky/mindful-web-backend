from fastapi.responses import JSONResponse

from ...core.http_responses import method_not_allowed_response
from ...schemas.auth import (
    LoginMethodNotAllowedSchema,
    LogoutMethodNotAllowedSchema,
    RefreshMethodNotAllowedSchema,
    RegisterMethodNotAllowedSchema,
    ResendCodeMethodNotAllowedSchema,
    VerifyMethodNotAllowedSchema,
    AnonymousMethodNotAllowedSchema,
    SessionMethodNotAllowedSchema,
)


def auth_register_method_not_allowed_response() -> JSONResponse:
    """Функция возврата ответа 405 Method Not Allowed для POST /auth/register.

    Returns:
        JSONResponse с ошибкой 405 Method Not Allowed.
    """
    return method_not_allowed_response(RegisterMethodNotAllowedSchema, allowed_method="POST")


def auth_login_method_not_allowed_response() -> JSONResponse:
    """Функция возврата ответа 405 Method Not Allowed для POST /auth/login.

    Returns:
        JSONResponse с ошибкой 405 Method Not Allowed.
    """
    return method_not_allowed_response(LoginMethodNotAllowedSchema, allowed_method="POST")


def auth_logout_method_not_allowed_response() -> JSONResponse:
    """Функция возврата ответа 405 Method Not Allowed для POST /auth/logout.

    Returns:
        JSONResponse с ошибкой 405 Method Not Allowed.
    """
    return method_not_allowed_response(LogoutMethodNotAllowedSchema, allowed_method="POST")


def auth_refresh_method_not_allowed_response() -> JSONResponse:
    """Функция возврата ответа 405 Method Not Allowed для POST /auth/refresh.

    Returns:
        JSONResponse с ошибкой 405 Method Not Allowed.
    """
    return method_not_allowed_response(RefreshMethodNotAllowedSchema, allowed_method="POST")


def auth_verify_method_not_allowed_response() -> JSONResponse:
    """Функция возврата ответа 405 Method Not Allowed для POST /auth/verify.

    Returns:
        JSONResponse с ошибкой 405 Method Not Allowed.
    """
    return method_not_allowed_response(VerifyMethodNotAllowedSchema, allowed_method="POST")


def auth_resend_code_method_not_allowed_response() -> JSONResponse:
    """Функция возврата ответа 405 Method Not Allowed для POST /auth/resend-code.

    Returns:
        JSONResponse с ошибкой 405 Method Not Allowed.
    """
    return method_not_allowed_response(ResendCodeMethodNotAllowedSchema, allowed_method="POST")


def auth_anonymous_method_not_allowed_response() -> JSONResponse:
    """Функция возврата ответа 405 Method Not Allowed для POST /auth/anonymous.

    Returns:
        JSONResponse с ошибкой 405 Method Not Allowed.
    """
    return method_not_allowed_response(AnonymousMethodNotAllowedSchema, allowed_method="POST")


def auth_session_method_not_allowed_response() -> JSONResponse:
    """Функция возврата ответа 405 Method Not Allowed для GET /auth/session.

    Returns:
        JSONResponse с ошибкой 405 Method Not Allowed.
    """
    return method_not_allowed_response(SessionMethodNotAllowedSchema, allowed_method="GET")
