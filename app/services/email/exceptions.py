from fastapi import status

from ...exceptions import AppException
from ...schemas.error_response_schema import ErrorCode


class EmailServiceException(AppException):
    """Базовое исключение сервиса email."""


# Исключения по статусу ответа
class EmailBadRequestException(EmailServiceException):
    """Ошибка запроса (400)."""

    status_code = status.HTTP_400_BAD_REQUEST
    error_code = ErrorCode.BUSINESS_VALIDATION_ERROR


# Исключения по статусу ответа
class EmailUnprocessableEntityException(EmailServiceException):
    """Бизнес ошибка (422)."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = ErrorCode.BUSINESS_VALIDATION_ERROR


class EmailInternalServerErrorException(EmailServiceException):
    """Непредвиденная ошибка (500)."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = ErrorCode.INTERNAL_ERROR


# Исключения для 422
class InvalidEmailFormatException(EmailUnprocessableEntityException):
    """Неверный формат email (422)."""

    error_code = "INVALID_EMAIL_FORMAT"


class InvalidVerificationCodeException(EmailUnprocessableEntityException):
    """Неверный формат кода подтверждения (422)."""

    error_code = "INVALID_VERIFICATION_CODE"


# Исключения для 500
class EmailSendFailedException(EmailInternalServerErrorException):
    """Ошибка отправки email (500)."""

    error_code = "EMAIL_SEND_FAILED"


class InvalidSMTPConfigException(EmailInternalServerErrorException):
    """Неверная конфигурация SMTP (500)."""

    error_code = "INVALID_SMTP_CONFIG"


class EmailServiceMessages:
    """Сообщения сервиса email."""

    EMAIL_CANNOT_BE_EMPTY = "Email cannot be empty"
    DEFAULT_FROM_EMAIL_CANNOT_BE_EMPTY = "Default sender email cannot be empty"
    INVALID_DEFAULT_FROM_EMAIL_FORMAT = "Invalid default sender email format"
    INVALID_EMAIL_FORMAT = "Invalid email format"
    VERIFICATION_CODE_CANNOT_BE_EMPTY = "Verification code cannot be empty"
    VERIFICATION_CODE_MUST_BE_DIGITS = "Verification code must contain only digits"
    VERIFICATION_CODE_MUST_BE_6_DIGITS = "Verification code must be 6 digits long"
    EMAIL_SEND_FAILED = "Failed to send email"
    SMTP_CONNECTION_ERROR = "Failed to connect to SMTP server"
    SMTP_AUTHENTICATION_ERROR = "SMTP authentication failed"
    SMTP_SEND_ERROR = "Failed to send email message"
    SMTP_UNEXPECTED_ERROR = "Unexpected error while sending email"
    SMTP_HOST_CANNOT_BE_EMPTY = "SMTP host cannot be empty"
    SMTP_PORT_INVALID = "SMTP port must be between 1 and 65535"
    SMTP_USER_CANNOT_BE_EMPTY = "SMTP user cannot be empty if provided"
    SMTP_PASSWORD_CANNOT_BE_EMPTY = "SMTP password cannot be empty if provided"
    SMTP_FROM_NAME_CANNOT_BE_EMPTY = "Default from name cannot be empty if provided"
    SMTP_TIMEOUT_INVALID = "SMTP timeout must be a positive integer"
    TEMPLATES_DIR_CANNOT_BE_EMPTY = "Templates directory path cannot be empty"
    TEMPLATES_DIR_NOT_EXISTS = "Templates directory does not exist"
    TEMPLATES_DIR_NOT_DIRECTORY = "Templates directory path is not a directory"
