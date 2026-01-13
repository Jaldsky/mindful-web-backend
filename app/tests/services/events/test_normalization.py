from unittest import TestCase

from app.services.events.normalizers import EventsServiceNormalizers


class TestEventsServiceNormalizers(TestCase):
    """Тесты нормализаторов events-сервиса."""

    def test_normalize_event_type_trim_and_lower(self):
        self.assertEqual(EventsServiceNormalizers.normalize_event_type("  Active  "), "active")

    def test_normalize_event_type_none(self):
        self.assertEqual(EventsServiceNormalizers.normalize_event_type(None), "")

    def test_normalize_domain_strips_protocol_www_path_port(self):
        self.assertEqual(
            EventsServiceNormalizers.normalize_domain("https://www.Example.COM:8080/some/path?q=1#x"),
            "example.com",
        )

    def test_normalize_domain_none(self):
        self.assertEqual(EventsServiceNormalizers.normalize_domain(None), "")
