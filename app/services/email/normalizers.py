from ..types import Email, VerificationCode
from ..normalizers import normalize_email


class EmailServiceNormalizers:
    """Класс с нормализаторами для email-сервиса."""

    @staticmethod
    def normalize_email(email: Email) -> Email:
        """Метод нормализации email адреса.

        Args:
            email: Email адрес для нормализации.

        Returns:
            Нормализованный email.
        """
        return normalize_email(email)

    @staticmethod
    def normalize_verification_code(code: VerificationCode) -> VerificationCode:
        """Метод нормализации кода подтверждения.

        Args:
            code: Код подтверждения для нормализации.

        Returns:
            Нормализованный код (без пробелов).
        """
        return (code or "").strip()
