from fastapi import status

from ..exceptions import EventsServiceException
from ....db.types import ExceptionMessage
from ....common.common import StringEnum
from ....schemas.events.events_error_code import EventsErrorCode
from ....schemas import ErrorDetailData, ErrorCode


class EventsBusinessValidationException(EventsServiceException):
    """Базовое исключение для ошибок валидации (422 Unprocessable Entity)."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = ErrorCode.BUSINESS_VALIDATION_ERROR


class EventsServerException(EventsServiceException):
    """Базовое исключение для серверных ошибок (500 Internal Server Error)."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = ErrorCode.INTERNAL_ERROR


# 422 Unprocessable Entity


class InvalidUserIdException(EventsBusinessValidationException):
    """Исключение при неверном формате User ID."""

    error_code = EventsErrorCode.INVALID_USER_ID

    def __init__(self, message: str, user_id: str):
        details = [
            ErrorDetailData(
                field="X-User-ID",
                message=message,
                value=user_id,
            )
        ]
        super().__init__(message=message, details=details)


class InvalidEventTypeException(EventsBusinessValidationException):
    """Исключение при неверном типе события."""

    error_code = EventsErrorCode.INVALID_EVENT_TYPE

    def __init__(self, message: str):
        details = [
            ErrorDetailData(
                field="data[].event",
                message=message,
                value=None,
            )
        ]
        super().__init__(message=message, details=details)


class InvalidDomainFormatException(EventsBusinessValidationException):
    """Исключение при неверном формате домена."""

    error_code = EventsErrorCode.INVALID_DOMAIN_FORMAT

    def __init__(self, message: str):
        details = [
            ErrorDetailData(
                field="data[].domain",
                message=message,
                value=None,
            )
        ]
        super().__init__(message=message, details=details)


class InvalidDomainLengthException(EventsBusinessValidationException):
    """Исключение при неверной длине домена."""

    error_code = EventsErrorCode.INVALID_DOMAIN_LENGTH

    def __init__(self, message: str):
        details = [
            ErrorDetailData(
                field="data[].domain",
                message=message,
                value=None,
            )
        ]
        super().__init__(message=message, details=details)


class TimestampInFutureException(EventsBusinessValidationException):
    """Исключение когда timestamp в будущем."""

    error_code = EventsErrorCode.TIMESTAMP_IN_FUTURE

    def __init__(self, message: str):
        details = [
            ErrorDetailData(
                field="data[].timestamp",
                message=message,
                value=None,
            )
        ]
        super().__init__(message=message, details=details)


class EmptyEventsListException(EventsBusinessValidationException):
    """Исключение при пустом списке событий."""


class TooManyEventsException(EventsBusinessValidationException):
    """Исключение при превышении максимального количества событий."""


# 500 Internal Server Error


class UserCreationFailedException(EventsServerException):
    """Исключение при ошибке создания/получения пользователя."""

    error_code = EventsErrorCode.USER_CREATION_FAILED


class EventsInsertFailedException(EventsServerException):
    """Исключение при ошибке вставки событий."""

    error_code = EventsErrorCode.EVENTS_INSERT_FAILED


class DataIntegrityViolationException(EventsServerException):
    """Исключение при нарушении целостности данных."""

    error_code = EventsErrorCode.DATA_INTEGRITY_VIOLATION


class TransactionFailedException(EventsServerException):
    """Исключение при ошибке транзакции базы данных."""

    error_code = EventsErrorCode.TRANSACTION_FAILED


class UnexpectedEventsException(EventsServerException):
    """Исключение при неожиданной ошибке обработки событий."""

    error_code = EventsErrorCode.TRANSACTION_FAILED


class EventsServiceMessages(StringEnum):
    """Перечисление сообщений об ошибках."""

    GET_OR_CREATE_USER_ERROR: ExceptionMessage = "Unable to create/find user {user_id}!"
    ADD_EVENTS_ERROR: ExceptionMessage = "Failed to insert event into the events table!"
    DATA_INTEGRITY_ERROR: ExceptionMessage = "Data integrity issue when saving events!"
    DATA_SAVE_ERROR: ExceptionMessage = "Database error while saving events!"
    UNEXPECTED_ERROR = "An unexpected error occurred while processing events!"
