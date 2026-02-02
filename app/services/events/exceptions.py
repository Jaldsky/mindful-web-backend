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

    error_code = EventsErrorCode.EMPTY_EVENTS_LIST


class TooManyEventsException(UnprocessableEntityException):
    """Слишком много событий (422)."""

    error_code = EventsErrorCode.TOO_MANY_EVENTS


class AnonEventsLimitExceededException(UnprocessableEntityException):
    """Слишком много событий (422)."""

    error_code = EventsErrorCode.ANON_EVENTS_LIMIT_EXCEEDED


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
