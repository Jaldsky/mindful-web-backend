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
