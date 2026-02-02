from ...core.common import StringEnum


class HealthcheckErrorCode(StringEnum):
    """Коды ошибок сервиса healthcheck."""

    HEALTHCHECK_SERVICE_ERROR = "HEALTHCHECK_SERVICE_ERROR"
