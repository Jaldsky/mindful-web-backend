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
from .exceptions import EmailSendFailedException
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

    def __init__(self, settings: EmailServiceSettings) -> None:
        """Магический метод инициализации транспорта SMTP.

        Args:
            settings: Настройки SMTP для подключения.
        """
        self._settings = settings

    def _determine_tls_mode(self) -> tuple[bool, bool]:
        """Приватный метод определения режима TLS соединения.

        Определяет тип TLS соединения на основе настроек:
        - Порт 465: прямое TLS/SSL соединение (use_tls=True в конструкторе SMTP)
        - Порт 587 и другие: STARTTLS (use_tls=False, затем starttls() вручную)
        - use_tls=False: без шифрования

        Returns:
            Кортеж (use_direct_tls, use_starttls)
        """
        use_direct_tls = self._settings.use_tls and self._settings.port == 465
        use_starttls = self._settings.use_tls and not use_direct_tls
        return use_direct_tls, use_starttls

    async def _establish_tls_connection(self, client: aiosmtplib.SMTP) -> None:
        """Приватный метод установки TLS соединения через STARTTLS.

        Процесс включает:
        1. Проверку необходимости отправки EHLO
        2. Проверку поддержки STARTTLS сервером
        3. Установку TLS соединения
        4. Обработку случая, когда TLS уже установлен

        Args:
            client: SMTP клиент для установки TLS.

        Raises:
            aiosmtplib.SMTPException: При ошибке установки TLS.
        """
        try:
            if client.is_ehlo_or_helo_needed:
                await client.ehlo()

            if client.supports_extension("starttls"):
                await client.starttls()
            else:
                logger.warning(f"SMTP server {self._settings.host}:{self._settings.port} does not support STARTTLS")
        except aiosmtplib.SMTPException as e:
            error_message = str(e)
            if "already using TLS" in error_message or "Connection already using TLS" in error_message:
                logger.debug(f"TLS already established for {self._settings.host}:{self._settings.port}")
            else:
                raise

    async def _authenticate(self, client: aiosmtplib.SMTP) -> None:
        """Приватный метод аутентификации на SMTP сервере.

        Args:
            client: SMTP клиент для аутентификации.

        Raises:
            aiosmtplib.SMTPAuthenticationError: При ошибке аутентификации.
        """
        if self._settings.user and self._settings.password:
            await client.login(self._settings.user, self._settings.password)

    async def send(self, message: MIMEMultipart, *, sender: Email, recipient: Email) -> None:
        """Метод отправки письма через SMTP сервер.

        Процесс отправки включает:
        1. Определение режима TLS соединения
        2. Подключение к SMTP серверу
        3. Установку TLS соединения (если требуется)
        4. Аутентификацию на сервере (если требуется)
        5. Отправку письма

        Args:
            message: MIME сообщение для отправки.
            sender: Email адрес отправителя.
            recipient: Email адрес получателя.

        Raises:
            EmailSendFailedException: При ошибке подключения, аутентификации или отправки email.
        """
        use_direct_tls, use_starttls = self._determine_tls_mode()

        try:
            async with aiosmtplib.SMTP(
                hostname=self._settings.host,
                port=self._settings.port,
                timeout=self._settings.timeout,
                use_tls=use_direct_tls,
                start_tls=False,
            ) as client:
                if use_starttls:
                    await self._establish_tls_connection(client)

                await self._authenticate(client)
                await client.send_message(message, sender=sender, recipients=recipient)

            logger.info(f"Email sent via SMTP: from {sender} to {recipient}")
        except aiosmtplib.SMTPConnectError:
            raise EmailSendFailedException(
                key="email.errors.smtp_connection_error",
                fallback="Failed to connect to SMTP server",
            )
        except aiosmtplib.SMTPAuthenticationError:
            raise EmailSendFailedException(
                key="email.errors.smtp_authentication_error",
                fallback="SMTP authentication failed",
            )
        except aiosmtplib.SMTPException:
            raise EmailSendFailedException(
                key="email.errors.smtp_send_error",
                fallback="Failed to send email message",
            )
        except Exception:
            raise EmailSendFailedException(
                key="email.errors.smtp_unexpected_error",
                fallback="Unexpected error while sending email",
            )
