from ..types import Email, VerificationCode


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
        return (email or "").strip().lower()

    @staticmethod
    def normalize_verification_code(code: VerificationCode) -> VerificationCode:
        """Метод нормализации кода подтверждения.
        Args:
            code: Код подтверждения для нормализации.
        Returns:
            Нормализованный код (без пробелов).
        """
        return (code or "").strip()
