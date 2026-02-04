from typing import Any
from fastapi import status

from .schemas import ErrorCode


class AppException(Exception):
    """Базовый класс для всех кастомных исключений приложения."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = ErrorCode.INTERNAL_ERROR

    def __init__(
        self,
        key: str | None = None,
        error_code: str | None = None,
        status_code: int | None = None,
        details: Any = None,
        translation_params: dict[str, Any] | None = None,
        fallback: str | None = None,
    ):
        self.key = key
        effective_fallback = fallback if fallback is not None else (key or "Unknown error")

        super().__init__(effective_fallback)
        self.fallback = effective_fallback
        self.translation_params = translation_params or {}
        if error_code:
            self.error_code = error_code
        if status_code:
            self.status_code = status_code
        self.details = details

    def get_response_content(self) -> dict:
        """Метод формирования тела ответа.

        Returns:
            Тела ответа.
        """
        details_data = self.details

        if isinstance(self.details, list):
            details_data = [
                (item.model_dump(mode="json") if hasattr(item, "model_dump") else item) for item in self.details
            ]
        elif hasattr(self.details, "model_dump"):
            details_data = self.details.model_dump(mode="json")

        return {
            "code": self.error_code,
            "message": self.fallback,
            "details": details_data,
        }


class UnsupportedLocaleException(AppException):
    """Неподдерживаемая локаль в заголовке Accept-Language (400)."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = ErrorCode.VALIDATION_ERROR
