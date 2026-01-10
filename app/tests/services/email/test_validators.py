from unittest import TestCase

from app.services.email.exceptions import (
    InvalidEmailFormatException,
    InvalidSMTPConfigException,
    InvalidVerificationCodeException,
)
from app.services.email.smtp import EmailServiceSettings
from app.services.email.validators import EmailServiceValidators


class TestEmailServiceValidators(TestCase):
    """Тесты валидации для EmailServiceValidators."""

    def test_validate_email_empty(self) -> None:
        with self.assertRaises(InvalidEmailFormatException):
            EmailServiceValidators.validate_email("")

    def test_validate_email_invalid_format(self) -> None:
        with self.assertRaises(InvalidEmailFormatException):
            EmailServiceValidators.validate_email("not-an-email")

    def test_validate_email_valid(self) -> None:
        try:
            EmailServiceValidators.validate_email("test@example.com")
        except InvalidEmailFormatException:
            self.fail("validate_email() raised InvalidEmailFormatException unexpectedly!")

    def test_validate_verification_code_empty(self) -> None:
        with self.assertRaises(InvalidVerificationCodeException):
            EmailServiceValidators.validate_verification_code("")

    def test_validate_verification_code_not_digits(self) -> None:
        with self.assertRaises(InvalidVerificationCodeException):
            EmailServiceValidators.validate_verification_code("12ab56")

    def test_validate_verification_code_wrong_length(self) -> None:
        with self.assertRaises(InvalidVerificationCodeException):
            EmailServiceValidators.validate_verification_code("12345")

    def test_validate_verification_code_valid(self) -> None:
        try:
            EmailServiceValidators.validate_verification_code("123456")
        except InvalidVerificationCodeException:
            self.fail("validate_verification_code() raised InvalidVerificationCodeException unexpectedly!")


class TestEmailServiceSettingsValidation(TestCase):
    """Тесты валидации настроек EmailServiceSettings."""

    def test_settings_invalid_host(self) -> None:
        with self.assertRaises(InvalidSMTPConfigException):
            EmailServiceSettings(
                host="  ",
                port=587,
                user=None,
                password=None,
                from_email="noreply@example.com",
                from_name=None,
                timeout=30,
                use_tls=False,
            )

    def test_settings_invalid_port(self) -> None:
        with self.assertRaises(InvalidSMTPConfigException):
            EmailServiceSettings(
                host="localhost",
                port=70000,
                user=None,
                password=None,
                from_email="noreply@example.com",
                from_name=None,
                timeout=30,
                use_tls=False,
            )

    def test_settings_invalid_timeout(self) -> None:
        with self.assertRaises(InvalidSMTPConfigException):
            EmailServiceSettings(
                host="localhost",
                port=587,
                user=None,
                password=None,
                from_email="noreply@example.com",
                from_name=None,
                timeout=0,
                use_tls=False,
            )

    def test_settings_invalid_from_email(self) -> None:
        with self.assertRaises(InvalidEmailFormatException):
            EmailServiceSettings(
                host="localhost",
                port=587,
                user=None,
                password=None,
                from_email="bad-email",
                from_name=None,
                timeout=30,
                use_tls=False,
            )

    def test_settings_normalizes_from_email(self) -> None:
        settings = EmailServiceSettings(
            host="localhost",
            port=587,
            user=None,
            password=None,
            from_email="  NOREPLY@EXAMPLE.COM ",
            from_name=None,
            timeout=30,
            use_tls=False,
        )
        self.assertEqual(settings.from_email, "noreply@example.com")
