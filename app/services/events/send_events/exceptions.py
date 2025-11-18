from ....db.types import ExceptionMessage
from ....common.common import FormException, StringEnum


class EventsServiceException(FormException):
    """Базовое исключение приложения."""


class UserCreationFailedException(EventsServiceException):
    """Исключение при ошибке создания/получения пользователя."""


class EventsInsertFailedException(EventsServiceException):
    """Исключение при ошибке вставки событий."""


class DataIntegrityViolationException(EventsServiceException):
    """Исключение при нарушении целостности данных."""


class TransactionFailedException(EventsServiceException):
    """Исключение при ошибке транзакции базы данных."""


class UnexpectedEventsException(EventsServiceException):
    """Исключение при неожиданной ошибке обработки событий."""


class InvalidEventTypeException(EventsServiceException):
    """Исключение при неверном типе события."""


class InvalidDomainFormatException(EventsServiceException):
    """Исключение при неверном формате домена."""


class InvalidDomainLengthException(EventsServiceException):
    """Исключение при неверной длине домена."""


class TimestampInFutureException(EventsServiceException):
    """Исключение когда timestamp в будущем."""


class InvalidUserIdException(EventsServiceException):
    """Исключение при неверном формате User ID."""


class EmptyEventsListException(EventsServiceException):
    """Исключение при пустом списке событий."""


class TooManyEventsException(EventsServiceException):
    """Исключение при превышении максимального количества событий."""


class EventsServiceMessages(StringEnum):
    """Перечисление сообщений об ошибках."""

    GET_OR_CREATE_USER_ERROR: ExceptionMessage = "Unable to create/find user {user_id}!"
    ADD_EVENTS_ERROR: ExceptionMessage = "Failed to insert event into the events table!"
    DATA_INTEGRITY_ERROR: ExceptionMessage = "Data integrity issue when saving events!"
    DATA_SAVE_ERROR: ExceptionMessage = "Database error while saving events!"
    UNEXPECTED_ERROR = "An unexpected error occurred while processing events!"
