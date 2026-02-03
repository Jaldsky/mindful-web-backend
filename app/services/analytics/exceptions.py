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


# Ошибки 500
class AnalyticsServiceException(InternalServerErrorException):
    """Ошибка сервиса аналитики (500)."""

    error_code = AnalyticsErrorCode.ANALYTICS_SERVICE_ERROR
