from ...core.common import StringEnum


class AnalyticsErrorCode(StringEnum):
    """Коды ошибок analytics."""

    INVALID_DATE_FORMAT = "USG_INVALID_DATE_FORMAT"
    INVALID_TIME_RANGE = "USG_INVALID_TIME_RANGE"
    INVALID_PAGE = "USG_INVALID_PAGE"

    ANALYTICS_SERVICE_ERROR = "ANALYTICS_SERVICE_ERROR"
