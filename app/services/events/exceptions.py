from fastapi import status

from ...exceptions import AppException
from ...schemas.events.events_error_code import EventsErrorCode


class EventsServiceException(AppException):
    """Базовое исключение сервиса events."""


# Исключения по статусу ответа
class EventsUnprocessableEntityException(EventsServiceException):
    """Бизнес ошибка (422)."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class EventsInternalServerErrorException(EventsServiceException):
    """Непредвиденная ошибка (500)."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


# Исключения для 422
class InvalidUserIdException(EventsUnprocessableEntityException):
    """Неверный формат User ID (422)."""

    error_code = EventsErrorCode.INVALID_USER_ID


class InvalidEventTypeException(EventsUnprocessableEntityException):
    """Неверный тип события (422)."""

    error_code = EventsErrorCode.INVALID_EVENT_TYPE


class InvalidDomainFormatException(EventsUnprocessableEntityException):
    """Неверный формат домена (422)."""

    error_code = EventsErrorCode.INVALID_DOMAIN_FORMAT


class InvalidDomainLengthException(EventsUnprocessableEntityException):
    """Неверная длина домена (422)."""

    error_code = EventsErrorCode.INVALID_DOMAIN_LENGTH


class TimestampInFutureException(EventsUnprocessableEntityException):
    """Timestamp в будущем (422)."""

    error_code = EventsErrorCode.TIMESTAMP_IN_FUTURE


class EmptyEventsListException(EventsUnprocessableEntityException):
    """Пустой список событий (422)."""


class TooManyEventsException(EventsUnprocessableEntityException):
    """Слишком много событий (422)."""


# Исключения для 500
class UserCreationFailedException(EventsInternalServerErrorException):
    """Ошибка создания/получения пользователя (500)."""

    error_code = EventsErrorCode.USER_CREATION_FAILED


class EventsInsertFailedException(EventsInternalServerErrorException):
    """Ошибка вставки событий (500)."""

    error_code = EventsErrorCode.EVENTS_INSERT_FAILED


class DataIntegrityViolationException(EventsInternalServerErrorException):
    """Нарушение целостности данных (500)."""

    error_code = EventsErrorCode.DATA_INTEGRITY_VIOLATION


class TransactionFailedException(EventsInternalServerErrorException):
    """Ошибка транзакции (500)."""

    error_code = EventsErrorCode.TRANSACTION_FAILED


class UnexpectedEventsException(EventsInternalServerErrorException):
    """Неожиданная ошибка обработки событий (500)."""

    error_code = EventsErrorCode.TRANSACTION_FAILED


class EventsServiceMessages:
    """Сообщения events-сервиса."""

    GET_OR_CREATE_USER_ERROR = "Unable to create/find user {user_id}!"
    ADD_EVENTS_ERROR = "Failed to insert event into the events table!"
    DATA_INTEGRITY_ERROR = "Data integrity issue when saving events!"
    DATA_SAVE_ERROR = "Database error while saving events!"
    UNEXPECTED_ERROR = "An unexpected error occurred while processing events!"
