from datetime import datetime, timedelta, timezone
from unittest import TestCase
from uuid import uuid4

from app.services.events.constants import MAX_DOMAIN_LENGTH, MAX_EVENTS_PER_REQUEST
from app.services.events.exceptions import (
    EmptyEventsListException,
    InvalidDomainFormatException,
    InvalidDomainLengthException,
    InvalidEventTypeException,
    InvalidUserIdException,
    TimestampInFutureException,
    TooManyEventsException,
)
from app.services.events.validators import EventsServiceValidators


class TestEventsServiceValidators(TestCase):
    """Тесты валидаторов events-сервиса."""

    def test_validate_event_type_invalid(self):
        with self.assertRaises(InvalidEventTypeException):
            EventsServiceValidators.validate_event_type("unknown")

    def test_validate_event_type_valid(self):
        try:
            EventsServiceValidators.validate_event_type("active")
        except InvalidEventTypeException:
            self.fail("validate_event_type() raised InvalidEventTypeException unexpectedly!")

    def test_validate_domain_empty(self):
        with self.assertRaises(InvalidDomainFormatException):
            EventsServiceValidators.validate_domain("")

    def test_validate_domain_no_dot(self):
        with self.assertRaises(InvalidDomainFormatException):
            EventsServiceValidators.validate_domain("localhost")

    def test_validate_domain_too_long(self):
        with self.assertRaises(InvalidDomainLengthException):
            # Домен должен содержать точку, иначе валидатор упадёт на проверке формата
            base = "a" * (MAX_DOMAIN_LENGTH - 2)  # + ".c" => MAX_DOMAIN_LENGTH
            too_long = f"{base}aa.c"  # +2 символа => MAX_DOMAIN_LENGTH + 2
            EventsServiceValidators.validate_domain(too_long)

    def test_validate_domain_invalid_chars(self):
        with self.assertRaises(InvalidDomainFormatException):
            EventsServiceValidators.validate_domain("examp!e.com")

    def test_validate_events_list_empty(self):
        with self.assertRaises(EmptyEventsListException):
            EventsServiceValidators.validate_events_list([])

    def test_validate_events_list_too_many(self):
        with self.assertRaises(TooManyEventsException):
            EventsServiceValidators.validate_events_list([object()] * (MAX_EVENTS_PER_REQUEST + 1))

    def test_validate_timestamp_in_future(self):
        future = datetime.now(timezone.utc) + timedelta(seconds=5)
        with self.assertRaises(TimestampInFutureException):
            EventsServiceValidators.validate_timestamp_not_in_future(future)

    def test_validate_user_id_header_invalid(self):
        with self.assertRaises(InvalidUserIdException):
            EventsServiceValidators.validate_user_id_header("not-a-uuid")

    def test_validate_user_id_header_valid(self):
        user_id = str(uuid4())
        self.assertEqual(EventsServiceValidators.validate_user_id_header(user_id), user_id)
