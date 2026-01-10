from unittest import TestCase
from app.services.auth.constants import MAX_PASSWORD_LENGTH, MAX_USERNAME_LENGTH
from app.services.auth.exceptions import (
    InvalidEmailFormatException,
    InvalidPasswordFormatException,
    InvalidUsernameFormatException,
)
from app.services.auth.validators import AuthServiceValidators


class TestAuthServiceValidators(TestCase):
    """Тесты валидаторов auth-сервиса."""

    def test_validate_username_too_short(self):
        """Тест валидации username слишком короткого."""
        with self.assertRaises(InvalidUsernameFormatException):
            AuthServiceValidators.validate_username("ab")

    def test_validate_username_too_long(self):
        """Тест валидации username слишком длинного."""
        long_username = "a" * (MAX_USERNAME_LENGTH + 1)
        with self.assertRaises(InvalidUsernameFormatException):
            AuthServiceValidators.validate_username(long_username)

    def test_validate_username_valid_min_length(self):
        """Тест валидации username минимальной длины."""
        try:
            AuthServiceValidators.validate_username("abc")
        except InvalidUsernameFormatException:
            self.fail("validate() raised InvalidUsernameFormatException unexpectedly!")

    def test_validate_username_valid_max_length(self):
        """Тест валидации username максимальной длины."""
        valid_username = "a" * MAX_USERNAME_LENGTH
        try:
            AuthServiceValidators.validate_username(valid_username)
        except InvalidUsernameFormatException:
            self.fail("validate() raised InvalidUsernameFormatException unexpectedly!")

    def test_validate_username_with_uppercase(self):
        """Тест валидации username с заглавными буквами (валидатор не нормализует)."""
        with self.assertRaises(InvalidUsernameFormatException):
            AuthServiceValidators.validate_username("TestUser")

    def test_validate_username_with_invalid_chars(self):
        """Тест валидации username с недопустимыми символами."""
        with self.assertRaises(InvalidUsernameFormatException):
            AuthServiceValidators.validate_username("test-user")

    def test_validate_username_starts_with_underscore(self):
        """Тест валидации username начинающегося с underscore."""
        with self.assertRaises(InvalidUsernameFormatException):
            AuthServiceValidators.validate_username("_testuser")

    def test_validate_username_ends_with_underscore(self):
        """Тест валидации username заканчивающегося на underscore."""
        with self.assertRaises(InvalidUsernameFormatException):
            AuthServiceValidators.validate_username("testuser_")

    def test_validate_email_empty(self):
        """Тест валидации пустого email."""
        with self.assertRaises(InvalidEmailFormatException):
            AuthServiceValidators.validate_email("")

    def test_validate_email_invalid_format(self):
        """Тест валидации email с неверным форматом."""
        with self.assertRaises(InvalidEmailFormatException):
            AuthServiceValidators.validate_email("invalid-email")

    def test_validate_email_valid(self):
        """Тест валидации валидного email."""
        try:
            AuthServiceValidators.validate_email("test@example.com")
        except InvalidEmailFormatException:
            self.fail("validate() raised InvalidEmailFormatException unexpectedly!")

    def test_validate_password_too_short(self):
        """Тест валидации password слишком короткого."""
        with self.assertRaises(InvalidPasswordFormatException):
            AuthServiceValidators.validate_password("pass123")

    def test_validate_password_too_long(self):
        """Тест валидации password слишком длинного."""
        long_password = "a" * (MAX_PASSWORD_LENGTH + 1) + "1"
        with self.assertRaises(InvalidPasswordFormatException):
            AuthServiceValidators.validate_password(long_password)

    def test_validate_password_no_letters(self):
        """Тест валидации password без букв."""
        with self.assertRaises(InvalidPasswordFormatException):
            AuthServiceValidators.validate_password("12345678")

    def test_validate_password_no_digits(self):
        """Тест валидации password без цифр."""
        with self.assertRaises(InvalidPasswordFormatException):
            AuthServiceValidators.validate_password("password")

    def test_validate_password_valid(self):
        """Тест валидации валидного password."""
        try:
            AuthServiceValidators.validate_password("password123")
        except InvalidPasswordFormatException:
            self.fail("validate() raised InvalidPasswordFormatException unexpectedly!")
