from fastapi import status

from ...exceptions import AppException


class HealthcheckException(AppException):
    """Базовое исключение сервиса healthcheck."""


# Исключения по статусу ответа
class HealthcheckServiceUnavailableException(HealthcheckException):
    """Сервис недоступен (503)."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class HealthcheckInternalServerErrorException(HealthcheckException):
    """Непредвиденная ошибка (500)."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class HealthcheckMessages:
    """Сообщения сервиса healthcheck."""

    SERVICE_UNAVAILABLE = "Service is unavailable"
    HEALTHCHECK_SERVICE_ERROR = "Healthcheck service error"
