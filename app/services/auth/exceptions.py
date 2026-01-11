from fastapi import status

from ...exceptions import AppException
from ...schemas.auth import AuthErrorCode


class AuthException(AppException):
    """Базовое исключение сервиса авторизации."""


# Исключения по статусу ответа
class AuthBadRequestException(AuthException):
    """Ошибка первичной валидации (400)."""

    status_code = status.HTTP_400_BAD_REQUEST


class AuthNotFoundException(AuthException):
    """Ресурс не найден (404)."""

    status_code = status.HTTP_404_NOT_FOUND


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


# Исключения для 401
class TokenInvalidException(AuthUnauthorizedException):
    """Невалидный токен (401)."""

    error_code = AuthErrorCode.TOKEN_INVALID


class TokenExpiredException(AuthUnauthorizedException):
    """Истёкший токен (401)."""

    error_code = AuthErrorCode.TOKEN_EXPIRED


class TokenMissingException(AuthUnauthorizedException):
    """Отсутствующий токен (401)."""

    error_code = AuthErrorCode.TOKEN_MISSING


class InvalidCredentialsException(AuthUnauthorizedException):
    """Неверные учетные данные (401)."""

    error_code = AuthErrorCode.INVALID_CREDENTIALS


# Исключения для 403
class EmailNotVerifiedException(AuthForbiddenException):
    """Email не подтверждён (403)."""

    error_code = AuthErrorCode.EMAIL_NOT_VERIFIED


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


# Исключения для 404
class UserNotFoundException(AuthNotFoundException):
    """Пользователь не найден (404)."""

    error_code = AuthErrorCode.USER_NOT_FOUND


# Исключения для 422
class EmailAlreadyVerifiedException(AuthUnprocessableEntityException):
    """Email уже подтверждён (422)."""

    error_code = AuthErrorCode.EMAIL_ALREADY_VERIFIED


class TooManyAttemptsException(AuthUnprocessableEntityException):
    """Слишком много попыток (422)."""

    error_code = AuthErrorCode.TOO_MANY_ATTEMPTS


class InvalidVerificationCodeFormatException(AuthUnprocessableEntityException):
    """Неверный формат кода подтверждения (422)."""

    error_code = AuthErrorCode.INVALID_VERIFICATION_CODE


class VerificationCodeExpiredException(AuthUnprocessableEntityException):
    """Код подтверждения истёк (422)."""

    error_code = AuthErrorCode.VERIFICATION_CODE_EXPIRED


class VerificationCodeInvalidException(AuthUnprocessableEntityException):
    """Код подтверждения неверный (422)."""

    error_code = AuthErrorCode.VERIFICATION_CODE_INVALID


class AuthMessages:
    """Сообщения сервиса авторизации."""

    USERNAME_EXISTS = "User with this username already exists"
    EMAIL_EXISTS = "User with this email already exists"
    EMAIL_SEND_FAILED = "Failed to send verification email"
    AUTH_SERVICE_ERROR = "Authentication service error"
    RESEND_CODE_DB_STAGE_ERROR = "Resend code failed due to a database error"
    RESEND_CODE_EMAIL_STAGE_ERROR = "Resend code failed while sending verification email"
    USER_NOT_FOUND = "User not found"
    EMAIL_ALREADY_VERIFIED = "Email is already verified"
    TOO_MANY_ATTEMPTS = "Too many attempts. Please try again later"
    CODE_INVALID = "Verification code is invalid"
    CODE_EXPIRED = "Verification code has expired"
    VERIFICATION_CODE_FORMAT_INVALID = "Verification code must be exactly 6 digits"
    EMAIL_CANNOT_BE_EMPTY = "Email cannot be empty"
    INVALID_EMAIL_FORMAT = "Invalid email format"
    USERNAME_LENGTH_INVALID = "Username length is invalid"
    USERNAME_INVALID_CHARS = "Username must contain only lowercase letters, numbers, and underscores"
    USERNAME_CANNOT_START_OR_END_WITH_UNDERSCORE = "Username cannot start or end with underscore"
    PASSWORD_LENGTH_INVALID = "Password length is invalid"
    PASSWORD_MUST_CONTAIN_LETTER = "Password must contain at least one letter"
    PASSWORD_MUST_CONTAIN_DIGIT = "Password must contain at least one digit"
    INVALID_CREDENTIALS = "Invalid credentials"
    EMAIL_NOT_VERIFIED = "Email is not verified"
    TOKEN_INVALID = "Token is invalid"
    TOKEN_EXPIRED = "Token has expired"
    TOKEN_MISSING = "Token is missing"
