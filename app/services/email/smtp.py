import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, NoReturn

import aiosmtplib
from email.mime.multipart import MIMEMultipart

from ...config import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    SMTP_FROM_EMAIL,
    SMTP_FROM_NAME,
    SMTP_USE_TLS,
)
from ..types import Email
from .constants import SMTP_TIMEOUT
from .exceptions import EmailServiceMessages, EmailSendFailedException
from .normalizers import EmailServiceNormalizers
from .types import (
    FromName,
    SMTPHost,
    SMTPPassword,
    SMTPPort,
    SMTPTimeout,
    SMTPUseTLS,
    SMTPUser,
)

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class EmailServiceSettings:
    """Настройки email-сервиса."""

    host: SMTPHost
    port: SMTPPort
    user: SMTPUser | None
    password: SMTPPassword | None
    from_email: Email
    from_name: FromName
    timeout: SMTPTimeout
    use_tls: SMTPUseTLS

    def __post_init__(self) -> None:
        """Магический метод пост-инициализации dataclass."""
        self.normalize()
        self.validate()

    @classmethod
    def from_defaults(cls, **overrides: Any) -> "EmailServiceSettings":
        """Фабричный метод создания настроек.
        Args:
            **overrides: Переопределения значений.
        Returns:
            Экземпляр EmailServiceSettings.
        """
        from_email = overrides.get("from_email", SMTP_FROM_EMAIL)
        return cls(
            host=overrides.get("host", SMTP_HOST),
            port=overrides.get("port", SMTP_PORT),
            user=overrides.get("user", SMTP_USER),
            password=overrides.get("password", SMTP_PASSWORD),
            from_email=EmailServiceNormalizers.normalize_email(from_email),
            from_name=overrides.get("from_name", SMTP_FROM_NAME),
            timeout=overrides.get("timeout", SMTP_TIMEOUT),
            use_tls=overrides.get("use_tls", SMTP_USE_TLS),
        )

    @property
    def templates_dir(self) -> Path:
        """Свойство получения пути до директории с HTML-шаблонами email.
        Returns:
            Путь к директории с шаблонами.
        """
        return Path(__file__).parent.joinpath("templates")

    def normalize(self) -> None:
        """Метод нормализации полей настроек email-сервиса."""
        normalized_email = EmailServiceNormalizers.normalize_email(self.from_email)
        if normalized_email != self.from_email:
            object.__setattr__(self, "from_email", normalized_email)

    def validate(self) -> None | NoReturn:
        """Метод валидации настроек email-сервиса.
        Raises:
            InvalidSMTPConfigException: При невалидных параметрах SMTP.
            InvalidEmailFormatException: При неверном формате from_email.
        """
        from .validators import EmailServiceSettingsValidator

        EmailServiceSettingsValidator.validate(self)


class SMTPTransport:
    """Класс отправки писем через SMTP."""

    messages: ClassVar[type[EmailServiceMessages]] = EmailServiceMessages

    def __init__(self, settings: EmailServiceSettings) -> None:
        """Магический метод инициализации транспорта SMTP.
        Args:
            settings: Настройки SMTP для подключения.
        """
        self._settings = settings

    async def send(self, message: MIMEMultipart, *, sender: Email, recipient: Email) -> None:
        """Метод отправки письма через SMTP сервер.
        Args:
            message: MIME сообщение для отправки.
            sender: Email адрес отправителя.
            recipient: Email адрес получателя.
        Raises:
            EmailSendFailedException: При ошибке подключения, аутентификации или отправки email.
        """
        try:
            async with aiosmtplib.SMTP(
                hostname=self._settings.host,
                port=self._settings.port,
                timeout=self._settings.timeout,
                use_tls=self._settings.use_tls,
            ) as client:
                if self._settings.user and self._settings.password:
                    await client.login(self._settings.user, self._settings.password)
                await client.send_message(message, sender=sender, recipients=recipient)
            logger.info(f"Email sent via SMTP: from {sender} to {recipient}")
        except aiosmtplib.SMTPConnectError:
            raise EmailSendFailedException(self.messages.SMTP_CONNECTION_ERROR)
        except aiosmtplib.SMTPAuthenticationError:
            raise EmailSendFailedException(self.messages.SMTP_AUTHENTICATION_ERROR)
        except aiosmtplib.SMTPException:
            raise EmailSendFailedException(self.messages.SMTP_SEND_ERROR)
        except Exception:
            raise EmailSendFailedException(self.messages.SMTP_UNEXPECTED_ERROR)
