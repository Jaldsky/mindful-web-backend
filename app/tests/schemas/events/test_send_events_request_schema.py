from datetime import datetime, timedelta, timezone
from unittest import TestCase

from app.schemas.events.send_events_request_schema import SendEventData, SendEventsRequestSchema
from app.services.events.exceptions import (
    EmptyEventsListException,
    InvalidDomainFormatException,
    InvalidDomainLengthException,
    InvalidEventTypeException,
    TimestampInFutureException,
    TooManyEventsException,
)


class TestSendEventData(TestCase):
    def setUp(self):
        self.base_payload = {
            "event": "active",
            "domain": "example.com",
            "timestamp": datetime.now(timezone.utc),
        }

    def test_valid_payload_passes(self):
        """Корректные данные успешно валидируются."""
        schema = SendEventData(**self.base_payload)

        self.assertEqual(schema.event, "active")
        self.assertEqual(schema.domain, "example.com")
        self.assertIsInstance(schema.timestamp, datetime)

    def test_invalid_event_type_raises_exception(self):
        """Неизвестный тип события отклоняется."""
        payload = {**self.base_payload, "event": "paused"}

        with self.assertRaises(InvalidEventTypeException):
            SendEventData(**payload)

    def test_domain_normalization(self):
        """Домен нормализуется (http/https, www, регистр, путь)."""
        payload = {**self.base_payload, "domain": "HTTPS://WWW.Example.COM/path?param=1"}

        schema = SendEventData(**payload)

        self.assertEqual(schema.domain, "example.com")

    def test_domain_without_dot_raises_exception(self):
        """Отсутствие точки в домене приводит к InvalidDomainFormatException."""
        payload = {**self.base_payload, "domain": "localhost"}

        with self.assertRaises(InvalidDomainFormatException):
            SendEventData(**payload)

    def test_domain_with_invalid_characters(self):
        """Недопустимые символы вызывают InvalidDomainFormatException."""
        payload = {**self.base_payload, "domain": "exa!mple.com"}

        with self.assertRaises(InvalidDomainFormatException):
            SendEventData(**payload)

    def test_domain_too_long_after_normalization(self):
        """Слишком длинный домен отклоняется после нормализации."""
        long_domain = "a" * 256
        payload = {**self.base_payload, "domain": f"http://{long_domain}.com"}

        with self.assertRaises(InvalidDomainLengthException):
            SendEventData(**payload)

    def test_timestamp_in_future_raises_exception(self):
        """Дата в будущем недопустима."""
        payload = {**self.base_payload, "timestamp": datetime.now(timezone.utc) + timedelta(days=1)}

        with self.assertRaises(TimestampInFutureException):
            SendEventData(**payload)


class TestSendEventsRequestSchema(TestCase):
    def setUp(self):
        now = datetime.now(timezone.utc)
        self.valid_event = {
            "event": "active",
            "domain": "example.com",
            "timestamp": now,
        }

    def test_valid_request(self):
        """Минимально корректный запрос проходит валидацию."""
        schema = SendEventsRequestSchema(data=[self.valid_event])

        self.assertEqual(len(schema.data), 1)
        self.assertIsInstance(schema.data[0], SendEventData)

    def test_empty_data_list_raises_exception(self):
        """Пустой список запрещён."""
        with self.assertRaises(EmptyEventsListException) as cm:
            SendEventsRequestSchema(data=[])
        self.assertEqual(str(cm.exception), "Events list cannot be empty")

    def test_data_list_exceeds_max_length(self):
        """Более 100 событий приводят к TooManyEventsException."""
        oversized = [self.valid_event for _ in range(101)]

        with self.assertRaises(TooManyEventsException) as cm:
            SendEventsRequestSchema(data=oversized)
        self.assertEqual(str(cm.exception), "Events list cannot contain more than 100 events")
