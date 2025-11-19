from pydantic import ValidationError

from ....db.types import ExceptionMessage
from ....common.common import FormException, StringEnum


class EventsServiceException(FormException):
    """Базовое исключение приложения."""


class EventsBadRequestException(EventsServiceException, ValidationError):
    """Базовое исключение для ошибок формата запроса (400 Bad Request)."""


class EventsValidationException(EventsServiceException):
    """Базовое исключение для ошибок валидации (422 Unprocessable Entity)."""


class EventsServerException(EventsServiceException):
    """Базовое исключение для серверных ошибок (500 Internal Server Error)."""


# 422 Unprocessable Entity


class InvalidUserIdException(EventsValidationException):
    """Исключение при неверном формате User ID."""


class InvalidEventTypeException(EventsValidationException):
    """Исключение при неверном типе события."""


class InvalidDomainFormatException(EventsValidationException):
    """Исключение при неверном формате домена."""


class InvalidDomainLengthException(EventsValidationException):
    """Исключение при неверной длине домена."""


class TimestampInFutureException(EventsValidationException):
    """Исключение когда timestamp в будущем."""


class EmptyEventsListException(EventsValidationException):
    """Исключение при пустом списке событий."""


class TooManyEventsException(EventsValidationException):
    """Исключение при превышении максимального количества событий."""


# 500 Internal Server Error


class UserCreationFailedException(EventsServerException):
    """Исключение при ошибке создания/получения пользователя."""


class EventsInsertFailedException(EventsServerException):
    """Исключение при ошибке вставки событий."""


class DataIntegrityViolationException(EventsServerException):
    """Исключение при нарушении целостности данных."""


class TransactionFailedException(EventsServerException):
    """Исключение при ошибке транзакции базы данных."""


class UnexpectedEventsException(EventsServerException):
    """Исключение при неожиданной ошибке обработки событий."""


class EventsServiceMessages(StringEnum):
    """Перечисление сообщений об ошибках."""

    GET_OR_CREATE_USER_ERROR: ExceptionMessage = "Unable to create/find user {user_id}!"
    ADD_EVENTS_ERROR: ExceptionMessage = "Failed to insert event into the events table!"
    DATA_INTEGRITY_ERROR: ExceptionMessage = "Data integrity issue when saving events!"
    DATA_SAVE_ERROR: ExceptionMessage = "Database error while saving events!"
    UNEXPECTED_ERROR = "An unexpected error occurred while processing events!"
