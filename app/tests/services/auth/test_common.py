import bcrypt
from unittest import TestCase

from app.services.auth.common import generate_verification_code, hash_password


class TestAuthCommon(TestCase):
    """Тесты общих утилит auth-сервиса."""

    def test_generate_verification_code_default(self):
        """Код по умолчанию: 6 цифр."""
        code = generate_verification_code()
        self.assertIsInstance(code, str)
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())

    def test_generate_verification_code_custom_length(self):
        """Код заданной длины: только цифры."""
        code = generate_verification_code(length=10)
        self.assertEqual(len(code), 10)
        self.assertTrue(code.isdigit())

    def test_hash_password_can_be_verified_by_bcrypt(self):
        """Хеш bcrypt должен проверяться функцией checkpw."""
        password = "password123"
        hashed = hash_password(password, rounds=4)  # ускоряем тест
        self.assertIsInstance(hashed, str)
        self.assertTrue(hashed.startswith("$2"))
        self.assertTrue(bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8")))
