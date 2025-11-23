from ...common.common import StringEnum


class UsageErrorCode(StringEnum):
    """Коды ошибок analytics usage."""

    # Ошибки валидации 422
    INVALID_DATE_FORMAT = "INVALID_DATE_FORMAT"
    INVALID_TIME_RANGE = "INVALID_TIME_RANGE"
    INVALID_PAGE = "INVALID_PAGE"
    INVALID_PAGE_SIZE = "INVALID_PAGE_SIZE"
    INVALID_EVENT_TYPE = "INVALID_EVENT_TYPE"

    # Ошибки сервера 500
    UNEXPECTED_ERROR = "UNEXPECTED_ERROR"
