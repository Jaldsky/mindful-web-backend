from unittest import TestCase

from app.services.email.builder import EmailMessageBuilder


class TestEmailMessageBuilder(TestCase):
    """Тесты сборщика EmailMessageBuilder."""

    def test_build_html_message_sets_headers_and_body(self) -> None:
        msg = EmailMessageBuilder.build_html_message(
            to_email="to@example.com",
            subject="Subject",
            html="<b>Hello</b>",
            from_email="from@example.com",
            from_name="Sender",
        )

        self.assertEqual(msg["To"], "to@example.com")
        self.assertEqual(msg["Subject"], "Subject")
        self.assertEqual(msg["From"], "Sender <from@example.com>")

        payload = msg.get_payload()
        self.assertTrue(payload)

        part = payload[0]
        self.assertEqual(part.get_content_type(), "text/html")
        decoded = part.get_payload(decode=True)
        self.assertIsNotNone(decoded)
        decoded_text = decoded.decode("utf-8", errors="replace")
        self.assertIn("Hello", decoded_text)
