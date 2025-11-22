from ....db.types import ExceptionMessage
from ....common.common import FormException, StringEnum


class UsageServiceException(FormException):
    """Базовое исключение сервиса аналитики использования."""


class UsageBusinessValidationException(UsageServiceException):
    """Базовое исключение для ошибок валидации (422 Unprocessable Entity)."""


class UsageServerException(UsageServiceException):
    """Базовое исключение для серверных ошибок (500 Internal Server Error)."""


# 422 Unprocessable Entity


class InvalidDateFormatException(UsageBusinessValidationException):
    """Исключение при неверном формате даты."""


class InvalidTimeRangeException(UsageBusinessValidationException):
    """Исключение при неверном временном диапазоне."""


class InvalidPageException(UsageBusinessValidationException):
    """Исключение при неверном номере страницы."""


class InvalidPageSizeException(UsageBusinessValidationException):
    """Исключение при неверном размере страницы."""


# 500 Internal Server Error


class DatabaseQueryFailedException(UsageServerException):
    """Исключение при ошибке запроса к базе данных."""


class DataProcessingFailedException(UsageServerException):
    """Исключение при ошибке обработки данных."""


class UnexpectedUsageException(UsageServerException):
    """Исключение при неожиданной ошибке обработки аналитики."""


class UsageServiceMessages(StringEnum):
    """Перечисление сообщений об ошибках."""

    INVALID_TIME_RANGE: ExceptionMessage = "Invalid time range: end time must be after start time!"
    DATABASE_QUERY_ERROR: ExceptionMessage = "Failed to query database for usage analytics!"
    DATA_PROCESSING_ERROR: ExceptionMessage = "Failed to process usage analytics data!"
    UNEXPECTED_ERROR: ExceptionMessage = "An unexpected error occurred while processing usage analytics!"
