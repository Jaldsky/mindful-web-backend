from fastapi import status
from app.exceptions import AppException
from ....db.types import ExceptionMessage
from ....common.common import StringEnum
from ....schemas.analytics.analytics_error_code import AnalyticsErrorCode
from ....schemas import ErrorCode as GlobalErrorCode
from ....schemas import ErrorDetailData


class UsageServiceException(AppException):
    """Базовое исключение сервиса аналитики использования."""


class UsageBusinessValidationException(UsageServiceException):
    """Базовое исключение для ошибок валидации (422 Unprocessable Entity)."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = "BUSINESS_VALIDATION_ERROR"


class UsageServerException(UsageServiceException):
    """Базовое исключение для серверных ошибок (500 Internal Server Error)."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "INTERNAL_ERROR"


# 422 Unprocessable Entity


class InvalidDateFormatException(UsageBusinessValidationException):
    """Исключение при неверном формате даты."""

    error_code = AnalyticsErrorCode.INVALID_DATE_FORMAT

    def __init__(self, message: str):
        field_name = "from/to"
        if "'from' date" in message.lower():
            field_name = "from"
        elif "'to' date" in message.lower():
            field_name = "to"

        details = [
            ErrorDetailData(
                field=field_name,
                message=message,
                value=None,
            )
        ]
        super().__init__(message=message, details=details)


class InvalidTimeRangeException(UsageBusinessValidationException):
    """Исключение при неверном временном диапазоне."""

    error_code = AnalyticsErrorCode.INVALID_TIME_RANGE

    def __init__(self, message: str):
        details = [
            ErrorDetailData(
                field="from/to",
                message=message,
                value=None,
            )
        ]
        super().__init__(message=message, details=details)


class InvalidPageException(UsageBusinessValidationException):
    """Исключение при неверном номере страницы."""

    error_code = AnalyticsErrorCode.INVALID_PAGE

    def __init__(self, message: str):
        details = [
            ErrorDetailData(
                field="page",
                message=message,
                value=None,
            )
        ]
        super().__init__(message=message, details=details)


class InvalidPageSizeException(UsageBusinessValidationException):
    """Исключение при неверном размере страницы."""

    error_code = AnalyticsErrorCode.INVALID_PAGE_SIZE

    def __init__(self, message: str):
        details = [
            ErrorDetailData(
                field="page_size",
                message=message,
                value=None,
            )
        ]
        super().__init__(message=message, details=details)


class InvalidEventTypeException(UsageBusinessValidationException):
    """Исключение при неверном типе события."""

    error_code = AnalyticsErrorCode.INVALID_EVENT_TYPE

    def __init__(self, message: str):
        details = [
            ErrorDetailData(
                field="event_type",
                message=message,
                value=None,
            )
        ]
        super().__init__(message=message, details=details)


# 500 Internal Server Error


class DatabaseQueryFailedException(UsageServerException):
    """Исключение при ошибке запроса к базе данных."""

    error_code = GlobalErrorCode.INTERNAL_ERROR  # Используем глобальный INTERNAL_ERROR


class DataProcessingFailedException(UsageServerException):
    """Исключение при ошибке обработки данных."""

    error_code = GlobalErrorCode.INTERNAL_ERROR  # Используем глобальный INTERNAL_ERROR


class UnexpectedUsageException(UsageServerException):
    """Исключение при неожиданной ошибке обработки аналитики."""

    error_code = GlobalErrorCode.INTERNAL_ERROR  # Используем глобальный INTERNAL_ERROR


class UsageServiceMessages(StringEnum):
    """Перечисление сообщений об ошибках."""

    INVALID_TIME_RANGE: ExceptionMessage = "Invalid time range: end time must be after start time!"
    DATABASE_QUERY_ERROR: ExceptionMessage = "Failed to query database for usage analytics!"
    DATA_PROCESSING_ERROR: ExceptionMessage = "Failed to process usage analytics data!"
    UNEXPECTED_ERROR: ExceptionMessage = "An unexpected error occurred while processing usage analytics!"
