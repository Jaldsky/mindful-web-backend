from fastapi import status

from ...exceptions import AppException
from ...schemas.auth import AuthErrorCode


class AuthException(AppException):
    """Базовое исключение сервиса авторизации."""


# Исключения по статусу ответа
class AuthBadRequestException(AuthException):
    """Ошибка первичной валидации (400)."""

    status_code = status.HTTP_400_BAD_REQUEST


class AuthUnauthorizedException(AuthException):
    """Ошибка авторизации (401)."""

    status_code = status.HTTP_401_UNAUTHORIZED


class AuthForbiddenException(AuthException):
    """Ошибка прав доступа (403)."""

    status_code = status.HTTP_403_FORBIDDEN


class AuthConflictException(AuthException):
    """Ошибка при конфликте (409)."""

    status_code = status.HTTP_409_CONFLICT


class AuthUnprocessableEntityException(AuthException):
    """Бизнес ошибка (422)."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class AuthInternalServerErrorException(AuthException):
    """Непредвиденная ошибка (500)."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


# Исключения для 409
class EmailAlreadyExistsException(AuthConflictException):
    """Email уже используется (409)."""

    error_code = AuthErrorCode.EMAIL_ALREADY_EXISTS


class UsernameAlreadyExistsException(AuthConflictException):
    """Логин уже занят (409)."""

    error_code = AuthErrorCode.USERNAME_ALREADY_EXISTS


# Исключения для 422
class InvalidUsernameFormatException(AuthUnprocessableEntityException):
    """Неверный формат логина (422)."""

    error_code = AuthErrorCode.INVALID_USERNAME_FORMAT


class InvalidEmailFormatException(AuthUnprocessableEntityException):
    """Неверный формат email (422)."""

    error_code = AuthErrorCode.INVALID_EMAIL_FORMAT


class InvalidPasswordFormatException(AuthUnprocessableEntityException):
    """Неверный формат пароля (422)."""

    error_code = AuthErrorCode.INVALID_PASSWORD_FORMAT


# Исключения для 500
class AuthServiceException(AuthInternalServerErrorException):
    """Ошибка сервиса авторизации (500)."""

    error_code = AuthErrorCode.AUTH_SERVICE_ERROR


class EmailSendFailedException(AuthInternalServerErrorException):
    """Ошибка сервиса email (500)."""

    error_code = AuthErrorCode.EMAIL_SEND_FAILED


class AuthMessages:
    """Сообщения сервиса авторизации."""

    USERNAME_EXISTS = "User with this username already exists"
    EMAIL_EXISTS = "User with this email already exists"
    EMAIL_SEND_FAILED = "Failed to send verification email"
    AUTH_SERVICE_ERROR = "Authentication service error"
    EMAIL_CANNOT_BE_EMPTY = "Email cannot be empty"
    INVALID_EMAIL_FORMAT = "Invalid email format"
    USERNAME_LENGTH_INVALID = "Username length is invalid"
    USERNAME_INVALID_CHARS = "Username must contain only lowercase letters, numbers, and underscores"
    USERNAME_CANNOT_START_OR_END_WITH_UNDERSCORE = "Username cannot start or end with underscore"
    PASSWORD_LENGTH_INVALID = "Password length is invalid"
    PASSWORD_MUST_CONTAIN_LETTER = "Password must contain at least one letter"
    PASSWORD_MUST_CONTAIN_DIGIT = "Password must contain at least one digit"
