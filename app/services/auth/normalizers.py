from .types import Password, Username
from ..types import Email
from ..normalizers import normalize_email


class AuthServiceNormalizers:
    """Класс с нормализаторами для auth-сервиса."""

    @staticmethod
    def normalize_username(username: Username) -> Username:
        """Метод нормализации логина.

        Args:
            username: Логин пользователя.

        Returns:
            Нормализованный логин.
        """
        return (username or "").strip().lower()

    @staticmethod
    def normalize_email(email: Email) -> Email:
        """Метод нормализации email.

        Args:
            email: Email адрес пользователя.

        Returns:
            Нормализованный email адрес.
        """
        return normalize_email(email)

    @staticmethod
    def normalize_password(password: Password) -> Password:
        """Метод нормализации пароля.

        Args:
            password: Пароль пользователя.

        Returns:
            Пароль или пустая строка, если None.
        """
        return password or ""
