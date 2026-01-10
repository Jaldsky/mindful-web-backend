from typing import ClassVar, NoReturn

from email_validator import EmailNotValidError

from .constants import (
    MAX_PASSWORD_LENGTH,
    MAX_USERNAME_LENGTH,
    MIN_PASSWORD_LENGTH,
    MIN_USERNAME_LENGTH,
)
from .exceptions import (
    AuthMessages,
    InvalidEmailFormatException,
    InvalidPasswordFormatException,
    InvalidUsernameFormatException,
)
from .types import Password, Username
from ..types import Email
from ..validators import validate_email_format


class AuthServiceValidators:
    """Валидаторы для auth-сервиса."""

    messages: ClassVar[type[AuthMessages]] = AuthMessages

    @classmethod
    def validate_username(cls, username: Username) -> None | NoReturn:
        """Метод валидации формата логина.

        Args:
            username: Логин пользователя для валидации.

        Raises:
            InvalidUsernameFormatException: Если username не соответствует требованиям.
        """
        if len(username) < MIN_USERNAME_LENGTH or len(username) > MAX_USERNAME_LENGTH:
            raise InvalidUsernameFormatException(cls.messages.USERNAME_LENGTH_INVALID)
        if not all(ch.islower() or ch.isdigit() or ch == "_" for ch in username):
            raise InvalidUsernameFormatException(cls.messages.USERNAME_INVALID_CHARS)
        if username.startswith("_") or username.endswith("_"):
            raise InvalidUsernameFormatException(cls.messages.USERNAME_CANNOT_START_OR_END_WITH_UNDERSCORE)

    @classmethod
    def validate_email(cls, email: Email) -> None | NoReturn:
        """Метод валидации формата email.

        Args:
            email: Email адрес пользователя для валидации.

        Raises:
            InvalidEmailFormatException: Если email имеет неверный формат или пустой.
        """
        if not email or not email.strip():
            raise InvalidEmailFormatException(cls.messages.EMAIL_CANNOT_BE_EMPTY)
        try:
            validate_email_format(email)
        except EmailNotValidError:
            raise InvalidEmailFormatException(cls.messages.INVALID_EMAIL_FORMAT)

    @classmethod
    def validate_password(cls, password: Password) -> None | NoReturn:
        """Метод валидации формата пароля.

        Args:
            password: Пароль пользователя для валидации.

        Raises:
            InvalidPasswordFormatException: Если password не соответствует требованиям.
        """
        if len(password) < MIN_PASSWORD_LENGTH or len(password) > MAX_PASSWORD_LENGTH:
            raise InvalidPasswordFormatException(cls.messages.PASSWORD_LENGTH_INVALID)
        if not any(ch.isalpha() for ch in password):
            raise InvalidPasswordFormatException(cls.messages.PASSWORD_MUST_CONTAIN_LETTER)
        if not any(ch.isdigit() for ch in password):
            raise InvalidPasswordFormatException(cls.messages.PASSWORD_MUST_CONTAIN_DIGIT)
