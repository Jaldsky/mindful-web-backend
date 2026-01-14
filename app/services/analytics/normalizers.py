from .types import DateStr


class AnalyticsServiceNormalizers:
    """Класс с нормализаторами для analytics-сервиса."""

    @staticmethod
    def normalize_date(date: DateStr) -> DateStr:
        """Метод нормализации строки даты.

        Важно: делает только trim пробелов и возвращает строку.
        Парсинг/валидация формата выполняются в валидаторах сервиса.

        Args:
            date: Дата в виде строки.

        Returns:
            Нормализованная строка даты.
        """
        return (date or "").strip()
