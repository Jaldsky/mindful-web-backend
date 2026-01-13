from .types import Domain, EventType


class EventsServiceNormalizers:
    """Класс с нормализаторами для events-сервиса."""

    @staticmethod
    def normalize_event_type(event: EventType) -> EventType:
        """Метод нормализации типа события.

        Args:
            event: Тип события для нормализации.

        Returns:
            Нормализованный тип события.
        """
        return (event or "").strip().lower()

    @staticmethod
    def normalize_domain(domain: Domain) -> Domain:
        """Метод нормализации домена.

        Args:
            domain: Домен для нормализации.

        Returns:
            Нормализованный домен.
        """
        v = (domain or "").strip().lower()
        if not v:
            return v

        if v.startswith("http://"):
            v = v[7:]
        elif v.startswith("https://"):
            v = v[8:]

        v = v.split("/")[0].split("?")[0].split("#")[0]
        v = v.split(":")[0]

        if v.startswith("www."):
            v = v[4:]

        return v
