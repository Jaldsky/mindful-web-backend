from fastapi import status

from ...exceptions import AppException
from ...schemas import ErrorCode
from ...schemas.analytics.analytics_error_code import AnalyticsErrorCode


class AnalyticsException(AppException):
    """Базовое исключение сервиса аналитики."""


class AnalyticsUnprocessableEntityException(AnalyticsException):
    """Бизнес ошибка (422)."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class AnalyticsInternalServerErrorException(AnalyticsException):
    """Непредвиденная ошибка (500)."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


# Ошибки 422
class InvalidDateFormatException(AnalyticsUnprocessableEntityException):
    """Исключение при неверном формате даты (422)."""

    error_code = AnalyticsErrorCode.INVALID_DATE_FORMAT


class InvalidTimeRangeException(AnalyticsUnprocessableEntityException):
    """Исключение при неверном временном диапазоне (422)."""

    error_code = AnalyticsErrorCode.INVALID_TIME_RANGE


class InvalidPageException(AnalyticsUnprocessableEntityException):
    """Исключение при неверном номере страницы (422)."""

    error_code = AnalyticsErrorCode.INVALID_PAGE


class InvalidPageSizeException(AnalyticsUnprocessableEntityException):
    """Исключение при неверном размере страницы (422)."""

    error_code = AnalyticsErrorCode.INVALID_PAGE_SIZE


class InvalidEventTypeException(AnalyticsUnprocessableEntityException):
    """Исключение при неверном типе события (422)."""

    error_code = AnalyticsErrorCode.INVALID_EVENT_TYPE


# Ошибки 500
class DatabaseQueryFailedException(AnalyticsInternalServerErrorException):
    """Исключение при ошибке запроса к базе данных (500)."""

    error_code = ErrorCode.DATABASE_ERROR


class UnexpectedUsageException(AnalyticsInternalServerErrorException):
    """Исключение при неожиданной ошибке обработки аналитики (500)."""

    error_code = ErrorCode.INTERNAL_ERROR


class AnalyticsUsageMessages:
    """Сообщения analytics usage."""

    INVALID_DATE_FORMAT = "Invalid date format"
    INVALID_PAGE_TYPE = "Invalid page value type"
    INVALID_PAGE = "Page must be greater than or equal to 1"
    INVALID_TIME_RANGE = "End time must be after start time!"

    DATABASE_QUERY_ERROR = "Failed to query database for usage analytics!"
    UNEXPECTED_ERROR = "An unexpected error occurred while processing usage analytics!"
