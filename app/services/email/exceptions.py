from .error_code import EmailErrorCode
from ..exceptions import (
    UnprocessableEntityException,
    InternalServerErrorException,
)


class InvalidVerificationCodeException(UnprocessableEntityException):
    """Неверный формат кода подтверждения (422)."""

    error_code = EmailErrorCode.INVALID_VERIFICATION_CODE


class InvalidEmailFormatException(UnprocessableEntityException):
    """Неверный формат кода подтверждения (422)."""

    error_code = EmailErrorCode.INVALID_EMAIL


# Исключения для 500
class EmailSendFailedException(InternalServerErrorException):
    """Ошибка отправки email (500)."""

    error_code = EmailErrorCode.EMAIL_SEND_FAILED


class InvalidSMTPConfigException(InternalServerErrorException):
    """Неверная конфигурация SMTP (500)."""

    error_code = EmailErrorCode.EMAIL_SEND_FAILED


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
