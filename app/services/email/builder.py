from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ..types import Email
from .constants import MIME_ENCODING_UTF8, MIME_SUBTYPE_HTML
from .types import FromName


class EmailMessageBuilder:
    """Сборка MIME-письма."""

    @staticmethod
    def _format_from_header(from_email: Email, from_name: FromName) -> str:
        """Форматирование заголовка From для MIME сообщения.
        Args:
            from_email: Email адрес отправителя.
            from_name: Имя отправителя.
        Returns:
            Отформатированная строка заголовка From.
        """
        if from_name:
            return f"{from_name} <{from_email}>"
        return from_email

    @staticmethod
    def build_html_message(
        *,
        to_email: Email,
        subject: str,
        html: str,
        from_email: Email,
        from_name: FromName,
        subtype: str = "alternative",
        html_subtype: str = MIME_SUBTYPE_HTML,
        charset: str = MIME_ENCODING_UTF8,
    ) -> MIMEMultipart:
        """Метод построения HTML MIME сообщения.
        Args:
            to_email: Email адрес получателя.
            subject: Тема письма.
            html: HTML контент письма.
            from_email: Email адрес отправителя.
            from_name: Имя отправителя.
            subtype: Подтип MIME сообщения.
            html_subtype: Подтип HTML контента.
            charset: Кодировка сообщения.
        Returns:
            Построенное MIME сообщение.
        """
        msg = MIMEMultipart(subtype)
        msg["Subject"] = subject
        msg["To"] = to_email
        msg["From"] = EmailMessageBuilder._format_from_header(from_email, from_name)
        msg.attach(MIMEText(html, html_subtype, charset))
        return msg
