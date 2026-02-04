from ..exceptions import (
    UnauthorizedException,
    ForbiddenException,
    ConflictException,
    UnprocessableEntityException,
    InternalServerErrorException,
)
from ...schemas.auth.auth_error_code import AuthErrorCode


# Исключения для 401
class TokenInvalidException(UnauthorizedException):
    """Невалидный токен (401)."""

    error_code = AuthErrorCode.TOKEN_INVALID


class TokenExpiredException(UnauthorizedException):
    """Истёкший токен (401)."""

    error_code = AuthErrorCode.TOKEN_EXPIRED


class TokenMissingException(UnauthorizedException):
    """Отсутствующий токен (401)."""

    error_code = AuthErrorCode.TOKEN_MISSING


class InvalidCredentialsException(UnauthorizedException):
    """Неверные учетные данные (401)."""

    error_code = AuthErrorCode.INVALID_CREDENTIALS


class UserNotFoundException(UnauthorizedException):
    """Пользователь не найден в системе (401)."""

    error_code = AuthErrorCode.USER_NOT_FOUND


# Исключения для 403
class EmailNotVerifiedException(ForbiddenException):
    """Email не подтверждён (403)."""

    error_code = AuthErrorCode.EMAIL_NOT_VERIFIED


# Исключения для 409
class EmailAlreadyExistsException(ConflictException):
    """Email уже используется (409)."""

    error_code = AuthErrorCode.EMAIL_ALREADY_EXISTS


class UsernameAlreadyExistsException(ConflictException):
    """Логин уже занят (409)."""

    error_code = AuthErrorCode.USERNAME_ALREADY_EXISTS


# Исключения для 422
class InvalidUsernameFormatException(UnprocessableEntityException):
    """Неверный формат логина (422)."""

    error_code = AuthErrorCode.INVALID_USERNAME_FORMAT


class InvalidEmailFormatException(UnprocessableEntityException):
    """Неверный формат email (422)."""

    error_code = AuthErrorCode.INVALID_EMAIL_FORMAT


class InvalidPasswordFormatException(UnprocessableEntityException):
    """Неверный формат пароля (422)."""

    error_code = AuthErrorCode.INVALID_PASSWORD_FORMAT


class EmailAlreadyVerifiedException(UnprocessableEntityException):
    """Email уже подтверждён (422)."""

    error_code = AuthErrorCode.EMAIL_ALREADY_VERIFIED


class TooManyAttemptsException(UnprocessableEntityException):
    """Слишком много попыток (422)."""

    error_code = AuthErrorCode.TOO_MANY_ATTEMPTS


class InvalidVerificationCodeFormatException(UnprocessableEntityException):
    """Неверный формат кода подтверждения (422)."""

    error_code = AuthErrorCode.INVALID_VERIFICATION_CODE


class VerificationCodeExpiredException(UnprocessableEntityException):
    """Код подтверждения истёк (422)."""

    error_code = AuthErrorCode.VERIFICATION_CODE_EXPIRED


class VerificationCodeInvalidException(UnprocessableEntityException):
    """Код подтверждения неверный (422)."""

    error_code = AuthErrorCode.VERIFICATION_CODE_INVALID


# Исключения для 500
class AuthServiceException(InternalServerErrorException):
    """Ошибка сервиса авторизации (500)."""

    error_code = AuthErrorCode.AUTH_SERVICE_ERROR


class EmailSendFailedException(InternalServerErrorException):
    """Ошибка сервиса email (500)."""

    error_code = AuthErrorCode.EMAIL_SEND_FAILED
