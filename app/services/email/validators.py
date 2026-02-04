from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, NoReturn
from email_validator import EmailNotValidError

from .smtp import EmailServiceSettings
from .constants import VERIFICATION_CODE_LENGTH
from .exceptions import InvalidEmailFormatException, InvalidSMTPConfigException, InvalidVerificationCodeException
from .types import FromName, SMTPHost, SMTPPassword, SMTPPort, SMTPTimeout, SMTPUser
from ..types import Email, VerificationCode
from ..validators import validate_email_format

if TYPE_CHECKING:
    from .renderer import TemplateRendererSettings


class EmailServiceValidators:
    """Валидаторы для email-сервиса."""

    @classmethod
    def validate_email(cls, email: Email) -> None | NoReturn:
        """Метод валидации формата email адреса.

        Args:
            email: Email адрес для валидации.

        Raises:
            InvalidEmailFormatException: Если email имеет неверный формат или пустой.
        """
        if not email:
            raise InvalidEmailFormatException(
                message_key="email.errors.email_cannot_be_empty",
                message="Email cannot be empty",
            )
        try:
            validate_email_format(email)
        except EmailNotValidError:
            raise InvalidEmailFormatException(
                message_key="email.errors.invalid_email_format",
                message="Invalid email format",
            )

    @classmethod
    def validate_verification_code(cls, code: VerificationCode) -> None | NoReturn:
        """Метод валидации формата кода подтверждения.

        Args:
            code: Код подтверждения для валидации.

        Raises:
            InvalidVerificationCodeException: Если code имеет неверный формат или пустой.
        """
        if not code:
            raise InvalidVerificationCodeException(
                message_key="email.errors.verification_code_cannot_be_empty",
                message="Verification code cannot be empty",
            )
        if not code.isdigit():
            raise InvalidVerificationCodeException(
                message_key="email.errors.verification_code_must_be_digits",
                message="Verification code must contain only digits",
            )
        if len(code) != VERIFICATION_CODE_LENGTH:
            raise InvalidVerificationCodeException(
                message_key="email.errors.verification_code_must_be_6_digits",
                message="Verification code must be 6 digits long",
            )


class EmailServiceSettingsValidator:
    """Валидатор настроек email-сервиса."""

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
            raise InvalidSMTPConfigException(
                message_key="email.errors.smtp_host_cannot_be_empty",
                message="SMTP host cannot be empty",
            )

    @classmethod
    def _validate_port(cls, port: SMTPPort) -> None | NoReturn:
        """Приватный метод валидации SMTP порта.

        Args:
            port: SMTP порт для валидации.

        Raises:
            InvalidSMTPConfigException: Если port невалидный.
        """
        if not isinstance(port, int) or port < 1 or port > 65535:
            raise InvalidSMTPConfigException(
                message_key="email.errors.smtp_port_invalid",
                message="SMTP port must be between 1 and 65535",
            )

    @classmethod
    def _validate_user(cls, user: SMTPUser | None) -> None | NoReturn:
        """Приватный метод валидации SMTP пользователя.

        Args:
            user: SMTP пользователь для валидации.

        Raises:
            InvalidSMTPConfigException: Если user указан, но пустой.
        """
        if user is not None and not str(user).strip():
            raise InvalidSMTPConfigException(
                message_key="email.errors.smtp_user_cannot_be_empty",
                message="SMTP user cannot be empty if provided",
            )

    @classmethod
    def _validate_password(cls, password: SMTPPassword | None) -> None | NoReturn:
        """Приватный метод валидации SMTP пароля.

        Args:
            password: SMTP пароль для валидации.

        Raises:
            InvalidSMTPConfigException: Если password указан, но пустой.
        """
        if password is not None and not str(password).strip():
            raise InvalidSMTPConfigException(
                message_key="email.errors.smtp_password_cannot_be_empty",
                message="SMTP password cannot be empty if provided",
            )

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
            raise InvalidSMTPConfigException(
                message_key="email.errors.smtp_from_name_cannot_be_empty",
                message="Default from name cannot be empty if provided",
            )

    @classmethod
    def _validate_timeout(cls, timeout: SMTPTimeout) -> None | NoReturn:
        """Приватный метод валидации SMTP таймаута.

        Args:
            timeout: SMTP таймаут для валидации.

        Raises:
            InvalidSMTPConfigException: Если timeout невалидный.
        """
        if not isinstance(timeout, int) or timeout <= 0:
            raise InvalidSMTPConfigException(
                message_key="email.errors.smtp_timeout_invalid",
                message="SMTP timeout must be a positive integer",
            )


class TemplateRendererSettingsValidator:
    """Валидатор настроек рендерера шаблонов."""

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
            raise InvalidSMTPConfigException(
                message_key="email.errors.templates_dir_cannot_be_empty",
                message="Templates directory path cannot be empty",
            )
        if not templates_dir.exists():
            raise InvalidSMTPConfigException(
                message_key="email.errors.templates_dir_not_exists",
                message="Templates directory does not exist",
            )
        if not templates_dir.is_dir():
            raise InvalidSMTPConfigException(
                message_key="email.errors.templates_dir_not_directory",
                message="Templates directory path is not a directory",
            )
