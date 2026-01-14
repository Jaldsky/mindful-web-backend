from ..exceptions import UnprocessableEntityException, InternalServerErrorException
from ...schemas.analytics.analytics_error_code import AnalyticsErrorCode


# Ошибки 422
class InvalidDateFormatException(UnprocessableEntityException):
    """Исключение при неверном формате даты (422)."""

    error_code = AnalyticsErrorCode.INVALID_DATE_FORMAT


class InvalidTimeRangeException(UnprocessableEntityException):
    """Исключение при неверном временном диапазоне (422)."""

    error_code = AnalyticsErrorCode.INVALID_TIME_RANGE


class InvalidPageException(UnprocessableEntityException):
    """Исключение при неверном номере страницы (422)."""

    error_code = AnalyticsErrorCode.INVALID_PAGE


class InvalidPageSizeException(UnprocessableEntityException):
    """Исключение при неверном размере страницы (422)."""

    error_code = AnalyticsErrorCode.INVALID_PAGE_SIZE


class InvalidEventTypeException(UnprocessableEntityException):
    """Исключение при неверном типе события (422)."""

    error_code = AnalyticsErrorCode.INVALID_EVENT_TYPE


# Ошибки 500
class AnalyticsServiceException(InternalServerErrorException):
    """Ошибка сервиса аналитики (500)."""

    error_code = AnalyticsErrorCode.ANALYTICS_SERVICE_ERROR


class AnalyticsUsageMessages:
    """Сообщения analytics usage."""

    INVALID_DATE_FORMAT = "Invalid date format"
    INVALID_PAGE_TYPE = "Invalid page value type"
    INVALID_PAGE = "Page must be greater than or equal to 1"
    INVALID_TIME_RANGE = "End time must be after start time!"

    DATABASE_QUERY_ERROR = "Failed to query database for usage analytics!"
    UNEXPECTED_ERROR = "An unexpected error occurred while processing usage analytics!"
