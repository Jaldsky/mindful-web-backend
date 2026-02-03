from ..exceptions import (
    ServiceUnavailableException,
)


class HealthcheckServiceUnavailableException(ServiceUnavailableException):
    """Сервис недоступен (503)."""
