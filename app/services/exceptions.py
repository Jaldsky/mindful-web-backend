from fastapi import status

from ..exceptions import AppException
from ..schemas import ErrorCode


# Исключения по статусу ответа
class BadRequestException(AppException):
    """Ошибка запроса (400)."""

    status_code = status.HTTP_400_BAD_REQUEST
    error_code = ErrorCode.VALIDATION_ERROR


class UnauthorizedException(AppException):
    """Ошибка авторизации (401)."""

    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = ErrorCode.UNAUTHORIZED


class ForbiddenException(AppException):
    """Ошибка прав доступа (403)."""

    status_code = status.HTTP_403_FORBIDDEN
    error_code = ErrorCode.FORBIDDEN


class NotFoundException(AppException):
    """Ресурс не найден (404)."""

    status_code = status.HTTP_404_NOT_FOUND
    error_code = ErrorCode.NOT_FOUND


class MethodNotAllowedException(AppException):
    """Метод не поддерживается (405)."""

    status_code = status.HTTP_405_METHOD_NOT_ALLOWED
    error_code = ErrorCode.METHOD_NOT_ALLOWED


class ConflictException(AppException):
    """Конфликт состояния ресурса (409)."""

    status_code = status.HTTP_409_CONFLICT
    error_code = ErrorCode.CONFLICT


class UnprocessableEntityException(AppException):
    """Бизнес ошибка (422)."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = ErrorCode.BUSINESS_VALIDATION_ERROR


class InternalServerErrorException(AppException):
    """Непредвиденная ошибка (500)."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = ErrorCode.INTERNAL_ERROR


class ServiceUnavailableException(AppException):
    """Непредвиденная ошибка (503)."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = ErrorCode.SERVICE_UNAVAILABLE


# Исключения для 500
class ServiceDatabaseErrorException(InternalServerErrorException):
    """Ошибка базы данных (500)."""

    error_code = ErrorCode.DATABASE_ERROR
