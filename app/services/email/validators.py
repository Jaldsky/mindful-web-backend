from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, NoReturn
from email_validator import EmailNotValidError, validate_email

from .smtp import EmailServiceSettings
from .constants import VERIFICATION_CODE_LENGTH
from .exceptions import (
    EmailServiceMessages,
    InvalidEmailFormatException,
    InvalidSMTPConfigException,
    InvalidVerificationCodeException,
)
from .types import FromName, SMTPHost, SMTPPassword, SMTPPort, SMTPTimeout, SMTPUser
from ..types import Email, VerificationCode

if TYPE_CHECKING:
    from .renderer import TemplateRendererSettings


class EmailServiceValidators:
    """Валидаторы для email-сервиса."""

    messages: ClassVar[type[EmailServiceMessages]] = EmailServiceMessages

    @classmethod
    def validate_email(cls, email: Email) -> None | NoReturn:
        """Метод валидации формата email адреса.

        Args:
            email: Email адрес для валидации.

        Raises:
            InvalidEmailFormatException: Если email имеет неверный формат или пустой.
        """
        if not email:
            raise InvalidEmailFormatException(cls.messages.EMAIL_CANNOT_BE_EMPTY)
        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError:
            raise InvalidEmailFormatException(cls.messages.INVALID_EMAIL_FORMAT)

    @classmethod
    def validate_verification_code(cls, code: VerificationCode) -> None | NoReturn:
        """Метод валидации формата кода подтверждения.

        Args:
            code: Код подтверждения для валидации.

        Raises:
            InvalidVerificationCodeException: Если code имеет неверный формат или пустой.
        """
        if not code:
            raise InvalidVerificationCodeException(cls.messages.VERIFICATION_CODE_CANNOT_BE_EMPTY)
        if not code.isdigit():
            raise InvalidVerificationCodeException(cls.messages.VERIFICATION_CODE_MUST_BE_DIGITS)
        if len(code) != VERIFICATION_CODE_LENGTH:
            raise InvalidVerificationCodeException(cls.messages.VERIFICATION_CODE_MUST_BE_6_DIGITS)


class EmailServiceSettingsValidator:
    """Валидатор настроек email-сервиса."""

    messages: ClassVar[type[EmailServiceMessages]] = EmailServiceMessages

    @classmethod
    def validate(cls, settings: EmailServiceSettings) -> None | NoReturn:
        """Метод валидации настроек email-сервиса.

        Args:
            settings: Настройки email-сервиса для валидации.

        Raises:
            InvalidSMTPConfigException: При невалидных параметрах SMTP.
            InvalidEmailFormatException: При неверном формате from_email.
        """
        cls._validate_host(settings.host)
        cls._validate_port(settings.port)
        cls._validate_user(settings.user)
        cls._validate_password(settings.password)
        cls._validate_from_email(settings.from_email)
        cls._validate_from_name(settings.from_name)
        cls._validate_timeout(settings.timeout)

    @classmethod
    def _validate_host(cls, host: SMTPHost) -> None | NoReturn:
        """Приватный метод валидации SMTP хоста.

        Args:
            host: SMTP хост для валидации.

        Raises:
            InvalidSMTPConfigException: Если host пустой или невалидный.
        """
        if not host or not str(host).strip():
            raise InvalidSMTPConfigException(cls.messages.SMTP_HOST_CANNOT_BE_EMPTY)

    @classmethod
    def _validate_port(cls, port: SMTPPort) -> None | NoReturn:
        """Приватный метод валидации SMTP порта.

        Args:
            port: SMTP порт для валидации.

        Raises:
            InvalidSMTPConfigException: Если port невалидный.
        """
        if not isinstance(port, int) or port < 1 or port > 65535:
            raise InvalidSMTPConfigException(cls.messages.SMTP_PORT_INVALID)

    @classmethod
    def _validate_user(cls, user: SMTPUser | None) -> None | NoReturn:
        """Приватный метод валидации SMTP пользователя.

        Args:
            user: SMTP пользователь для валидации.

        Raises:
            InvalidSMTPConfigException: Если user указан, но пустой.
        """
        if user is not None and not str(user).strip():
            raise InvalidSMTPConfigException(cls.messages.SMTP_USER_CANNOT_BE_EMPTY)

    @classmethod
    def _validate_password(cls, password: SMTPPassword | None) -> None | NoReturn:
        """Приватный метод валидации SMTP пароля.

        Args:
            password: SMTP пароль для валидации.

        Raises:
            InvalidSMTPConfigException: Если password указан, но пустой.
        """
        if password is not None and not str(password).strip():
            raise InvalidSMTPConfigException(cls.messages.SMTP_PASSWORD_CANNOT_BE_EMPTY)

    @classmethod
    def _validate_from_email(cls, from_email: Email) -> None | NoReturn:
        """Приватный метод валидации email адреса отправителя.

        Args:
            from_email: Email адрес отправителя для валидации.

        Raises:
            InvalidEmailFormatException: Если from_email имеет неверный формат или пустой.
        """
        EmailServiceValidators.validate_email(from_email)

    @classmethod
    def _validate_from_name(cls, from_name: FromName) -> None | NoReturn:
        """Приватный метод валидации имени отправителя.

        Args:
            from_name: Имя отправителя для валидации.

        Raises:
            InvalidSMTPConfigException: Если from_name указан, но пустой.
        """
        if from_name is not None and not str(from_name).strip():
            raise InvalidSMTPConfigException(cls.messages.SMTP_FROM_NAME_CANNOT_BE_EMPTY)

    @classmethod
    def _validate_timeout(cls, timeout: SMTPTimeout) -> None | NoReturn:
        """Приватный метод валидации SMTP таймаута.

        Args:
            timeout: SMTP таймаут для валидации.

        Raises:
            InvalidSMTPConfigException: Если timeout невалидный.
        """
        if not isinstance(timeout, int) or timeout <= 0:
            raise InvalidSMTPConfigException(cls.messages.SMTP_TIMEOUT_INVALID)


class TemplateRendererSettingsValidator:
    """Валидатор настроек рендерера шаблонов."""

    messages: ClassVar[type[EmailServiceMessages]] = EmailServiceMessages

    @classmethod
    def validate(cls, settings: "TemplateRendererSettings") -> None | NoReturn:
        """Метод валидации настроек рендерера шаблонов.

        Args:
            settings: Настройки рендерера шаблонов для валидации.

        Raises:
            InvalidSMTPConfigException: При невалидном пути к директории шаблонов.
        """
        cls._validate_templates_dir(settings.templates_dir)

    @classmethod
    def _validate_templates_dir(cls, templates_dir: Path) -> None | NoReturn:
        """Приватный метод валидации пути к директории шаблонов.

        Args:
            templates_dir: Путь к директории шаблонов для валидации.

        Raises:
            InvalidSMTPConfigException: Если templates_dir пустой, не существует или не является директорией.
        """
        if not templates_dir:
            raise InvalidSMTPConfigException(cls.messages.TEMPLATES_DIR_CANNOT_BE_EMPTY)
        if not templates_dir.exists():
            raise InvalidSMTPConfigException(cls.messages.TEMPLATES_DIR_NOT_EXISTS)
        if not templates_dir.is_dir():
            raise InvalidSMTPConfigException(cls.messages.TEMPLATES_DIR_NOT_DIRECTORY)
