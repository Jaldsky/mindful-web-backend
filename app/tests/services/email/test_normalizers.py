from unittest import TestCase

from app.services.email.normalizers import EmailServiceNormalizers


class TestEmailServiceNormalizers(TestCase):
    """Тесты нормализации для EmailServiceNormalizers."""

    def test_normalize_email_strips_and_lowercases(self) -> None:
        self.assertEqual(EmailServiceNormalizers.normalize_email("  Test@Example.COM  "), "test@example.com")

    def test_normalize_email_none(self) -> None:
        self.assertEqual(EmailServiceNormalizers.normalize_email(None), "")

    def test_normalize_verification_code_strips(self) -> None:
        self.assertEqual(EmailServiceNormalizers.normalize_verification_code("  123456  "), "123456")

    def test_normalize_verification_code_none(self) -> None:
        self.assertEqual(EmailServiceNormalizers.normalize_verification_code(None), "")
