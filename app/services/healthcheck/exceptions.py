from ..exceptions import (
    ServiceUnavailableException,
)


class HealthcheckServiceUnavailableException(ServiceUnavailableException):
    """Сервис недоступен (503)."""


class HealthcheckMessages:
    """Сообщения сервиса healthcheck."""

    SERVICE_UNAVAILABLE = "Service is unavailable"
    HEALTHCHECK_SERVICE_ERROR = "Healthcheck service error"
