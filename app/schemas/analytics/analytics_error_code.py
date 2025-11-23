from ...common.common import StringEnum


class AnalyticsErrorCode(StringEnum):
    """Коды ошибок analytics."""

    # Ошибки валидации 422
    # Ошибки для usage
    INVALID_DATE_FORMAT = "USG_INVALID_DATE_FORMAT"
    INVALID_TIME_RANGE = "USG_INVALID_TIME_RANGE"
    INVALID_PAGE = "USG_INVALID_PAGE"
    INVALID_PAGE_SIZE = "USG_INVALID_PAGE_SIZE"
    INVALID_EVENT_TYPE = "USG_INVALID_EVENT_TYPE"
