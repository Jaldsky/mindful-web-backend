from unittest import TestCase
from uuid import UUID, uuid1, uuid3, uuid4, uuid5, NAMESPACE_DNS
from pydantic import ValidationError

from app.schemas.events.send.user_id_header_schema import SendEventsUserIdHeaderSchema
from app.services.events.send_events.exceptions import InvalidUserIdException


class TestSendEventsUserIdHeaderSchema(TestCase):
    def test_default_factory_generates_uuid4(self):
        """Без входных данных создаётся валидный UUID4."""
        schema = SendEventsUserIdHeaderSchema()

        generated_uuid = UUID(schema.x_user_id)
        self.assertEqual(generated_uuid.version, 4)

    def test_valid_uuid4_remains_unchanged(self):
        """Переданный валидный UUID4 возвращается без изменений."""
        value = str(uuid4())

        schema = SendEventsUserIdHeaderSchema(x_user_id=value)

        self.assertEqual(schema.x_user_id, value)

    def test_uppercase_uuid4_is_allowed(self):
        """Строка UUID4 в верхнем регистре корректно принимается."""
        value = str(uuid4()).upper()

        schema = SendEventsUserIdHeaderSchema(x_user_id=value)

        self.assertEqual(schema.x_user_id, value)

    def test_invalid_uuid_versions_raise_exception(self):
        """UUID других версий (1,3,5) отклоняются."""
        invalid_versions = [
            str(uuid1()),
            str(uuid3(NAMESPACE_DNS, "example.com")),
            str(uuid5(NAMESPACE_DNS, "example.com")),
        ]

        for invalid in invalid_versions:
            with self.subTest(invalid=invalid):
                with self.assertRaises(InvalidUserIdException) as cm:
                    SendEventsUserIdHeaderSchema(x_user_id=invalid)

                self.assertEqual(str(cm.exception), "X-User-ID must be a valid UUID4 string")

    def test_invalid_strings_raise_exception(self):
        """Произвольные строки и пустые значения отклоняются."""
        invalid_values = [
            "not-a-uuid",
            "123",
            "f47ac10b-58cc-4372-a567-0e02b2c3d47",
            "f47ac10b-58cc-4372-a567-0e02b2c3d479-extra",
            "",
        ]

        for invalid in invalid_values:
            with self.subTest(invalid=invalid):
                with self.assertRaises(InvalidUserIdException) as cm:
                    SendEventsUserIdHeaderSchema(x_user_id=invalid)

                self.assertEqual(str(cm.exception), "X-User-ID must be a valid UUID4 string")

    def test_none_value_raises_validation_error(self):
        """None для строкового поля отклоняется на уровне Pydantic."""
        with self.assertRaises(ValidationError):
            SendEventsUserIdHeaderSchema(x_user_id=None)
