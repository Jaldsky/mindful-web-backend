from ..exceptions import (
    UnprocessableEntityException,
    InternalServerErrorException,
)
from ...schemas.events.events_error_code import EventsErrorCode


# Исключения для 422
class InvalidUserIdException(UnprocessableEntityException):
    """Неверный формат User ID (422)."""

    error_code = EventsErrorCode.INVALID_USER_ID


class InvalidEventTypeException(UnprocessableEntityException):
    """Неверный тип события (422)."""

    error_code = EventsErrorCode.INVALID_EVENT_TYPE


class InvalidDomainFormatException(UnprocessableEntityException):
    """Неверный формат домена (422)."""

    error_code = EventsErrorCode.INVALID_DOMAIN_FORMAT


class InvalidDomainLengthException(UnprocessableEntityException):
    """Неверная длина домена (422)."""

    error_code = EventsErrorCode.INVALID_DOMAIN_LENGTH


class TimestampInFutureException(UnprocessableEntityException):
    """Timestamp в будущем (422)."""

    error_code = EventsErrorCode.TIMESTAMP_IN_FUTURE


class EmptyEventsListException(UnprocessableEntityException):
    """Пустой список событий (422)."""


class TooManyEventsException(UnprocessableEntityException):
    """Слишком много событий (422)."""


# Исключения для 500
class UserCreationFailedException(InternalServerErrorException):
    """Ошибка создания/получения пользователя (500)."""

    error_code = EventsErrorCode.USER_CREATION_FAILED


class EventsInsertFailedException(InternalServerErrorException):
    """Ошибка вставки событий (500)."""

    error_code = EventsErrorCode.EVENTS_INSERT_FAILED


class DataIntegrityViolationException(InternalServerErrorException):
    """Нарушение целостности данных (500)."""

    error_code = EventsErrorCode.DATA_INTEGRITY_VIOLATION


class TransactionFailedException(InternalServerErrorException):
    """Ошибка транзакции (500)."""

    error_code = EventsErrorCode.TRANSACTION_FAILED


class UnexpectedEventsException(InternalServerErrorException):
    """Неожиданная ошибка обработки событий (500)."""

    error_code = EventsErrorCode.TRANSACTION_FAILED


class EventsServiceMessages:
    """Сообщения events-сервиса."""

    GET_OR_CREATE_USER_ERROR = "Unable to create/find user {user_id}!"
    ADD_EVENTS_ERROR = "Failed to insert event into the events table!"
    DATA_INTEGRITY_ERROR = "Data integrity issue when saving events!"
    DATA_SAVE_ERROR = "Database error while saving events!"
    UNEXPECTED_ERROR = "An unexpected error occurred while processing events!"
