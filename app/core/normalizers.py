"""Нормализаторы для core: локаль и др."""

from ..config import DEFAULT_LOCALE


class LocaleNormalizer:
    """Класс нормализации строки локали из параметра пользователя (например Accept-Language)."""

    @staticmethod
    def normalize(locale: str, default: str = DEFAULT_LOCALE) -> str:
        """Оставляет только базовый тег локали (en-US -> en).

        Вызывать при получении локали от пользователя (middleware, dependency),
        чтобы дальше по коду использовать уже нормализованное значение.

        Args:
            locale: Строка локали (может быть пустой или с суффиксом, например en-US).
            default: Локаль по умолчанию при пустом значении.

        Returns:
            Нормализованная локаль (нижний регистр, без суффикса, или default).
        """
        if not locale or not locale.strip():
            return default
        return locale.strip().split("-")[0].lower()
