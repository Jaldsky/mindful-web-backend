from unittest import TestCase

from app.services.auth.normalizers import AuthServiceNormalizers


class TestAuthServiceNormalizers(TestCase):
    """Тесты нормализаторов auth-сервиса."""

    def test_normalize_username_trim_and_lower(self):
        self.assertEqual(AuthServiceNormalizers.normalize_username("  TestUser  "), "testuser")

    def test_normalize_username_none(self):
        self.assertEqual(AuthServiceNormalizers.normalize_username(None), "")

    def test_normalize_email_trim_and_lower(self):
        self.assertEqual(AuthServiceNormalizers.normalize_email("  Test@Example.COM  "), "test@example.com")

    def test_normalize_email_none(self):
        self.assertEqual(AuthServiceNormalizers.normalize_email(None), "")

    def test_normalize_password_keeps_value(self):
        self.assertEqual(AuthServiceNormalizers.normalize_password("password123"), "password123")

    def test_normalize_password_none(self):
        self.assertEqual(AuthServiceNormalizers.normalize_password(None), "")
