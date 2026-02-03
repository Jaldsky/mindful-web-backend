from typing import NoReturn

from email_validator import EmailNotValidError

from .constants import (
    MAX_PASSWORD_LENGTH,
    MAX_USERNAME_LENGTH,
    MIN_PASSWORD_LENGTH,
    MIN_USERNAME_LENGTH,
)
from .exceptions import (
    InvalidEmailFormatException,
    InvalidPasswordFormatException,
    TokenInvalidException,
    InvalidUsernameFormatException,
    InvalidVerificationCodeFormatException,
)
from .types import Password, RefreshToken, AccessToken
from ..types import Email, VerificationCode, Username
from ..validators import validate_email_format


class AuthServiceValidators:
    """Валидаторы для auth-сервиса."""

    @classmethod
    def validate_username(cls, username: Username) -> None | NoReturn:
        """Метод валидации формата логина.

        Args:
            username: Логин пользователя для валидации.

        Raises:
            InvalidUsernameFormatException: Если username не соответствует требованиям.
        """
        if len(username) < MIN_USERNAME_LENGTH or len(username) > MAX_USERNAME_LENGTH:
            raise InvalidUsernameFormatException("auth.errors.username_length_invalid")
        if not all(ch.islower() or ch.isdigit() or ch == "_" for ch in username):
            raise InvalidUsernameFormatException("auth.errors.username_invalid_chars")
        if username.startswith("_") or username.endswith("_"):
            raise InvalidUsernameFormatException("auth.errors.username_cannot_start_or_end_with_underscore")

    @classmethod
    def validate_email(cls, email: Email) -> None | NoReturn:
        """Метод валидации формата email.

        Args:
            email: Email адрес пользователя для валидации.

        Raises:
            InvalidEmailFormatException: Если email имеет неверный формат или пустой.
        """
        if not email or not email.strip():
            raise InvalidEmailFormatException("auth.errors.email_cannot_be_empty")
        try:
            validate_email_format(email)
        except EmailNotValidError:
            raise InvalidEmailFormatException("auth.errors.invalid_email_format")

    @classmethod
    def validate_password(cls, password: Password) -> None | NoReturn:
        """Метод валидации формата пароля.

        Args:
            password: Пароль пользователя для валидации.

        Raises:
            InvalidPasswordFormatException: Если password не соответствует требованиям.
        """
        if len(password) < MIN_PASSWORD_LENGTH or len(password) > MAX_PASSWORD_LENGTH:
            raise InvalidPasswordFormatException("auth.errors.password_length_invalid")
        if not any(ch.isalpha() for ch in password):
            raise InvalidPasswordFormatException("auth.errors.password_must_contain_letter")
        if not any(ch.isdigit() for ch in password):
            raise InvalidPasswordFormatException("auth.errors.password_must_contain_digit")

    @classmethod
    def validate_verification_code(cls, code: VerificationCode) -> None | NoReturn:
        """Метод валидации формата кода подтверждения.

        Args:
            code: Код подтверждения.

        Raises:
            InvalidVerificationCodeFormatException: Если code не валидный.
        """
        if len(code) != 6 or not code.isdigit():
            raise InvalidVerificationCodeFormatException("auth.errors.verification_code_format_invalid")

    @classmethod
    def validate_jwt_token(cls, token: RefreshToken | AccessToken) -> None | NoReturn:
        """Метод валидации токена.

        Args:
            token: JWT токен access или refresh.

        Raises:
            TokenInvalidException: Если токен пустой.
        """
        if not token:
            raise TokenInvalidException("auth.errors.token_invalid")
