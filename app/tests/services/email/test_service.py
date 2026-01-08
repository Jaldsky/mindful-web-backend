import asyncio
from unittest import TestCase
from unittest.mock import AsyncMock, Mock

from app.services.email.constants import VERIFICATION_CODE_TEMPLATE
from app.services.email.exceptions import InvalidEmailFormatException, InvalidVerificationCodeException
from app.services.email.service import EmailService
from app.services.email.smtp import EmailServiceSettings


class TestEmailServiceSendVerificationCode(TestCase):
    """Тесты EmailService.send_verification_code."""

    def _run_async(self, coro):
        return asyncio.run(coro)

    def _service(self) -> EmailService:
        settings = EmailServiceSettings(
            host="localhost",
            port=587,
            user=None,
            password=None,
            from_email="noreply@example.com",
            from_name="Mindful",
            timeout=30,
            use_tls=False,
        )
        return EmailService(settings=settings)

    def test_send_verification_code_success_normalizes_recipient_and_sends(self) -> None:
        service = self._service()

        renderer = Mock()
        renderer.render = Mock(return_value="<html>CODE: 123456</html>")
        service._renderer = renderer

        transport = Mock()
        transport.send = AsyncMock()
        service._transport = transport

        self._run_async(service.send_verification_code(to_email="  Test@Example.COM  ", code=" 123456 "))

        renderer.render.assert_called_once_with(VERIFICATION_CODE_TEMPLATE, context={"code": "123456"})
        transport.send.assert_awaited_once()

        args, kwargs = transport.send.await_args
        message = args[0]
        self.assertEqual(kwargs["recipient"], "test@example.com")
        self.assertEqual(kwargs["sender"], "noreply@example.com")
        self.assertEqual(message["To"], "test@example.com")

    def test_send_verification_code_invalid_to_email_raises_and_does_not_send(self) -> None:
        service = self._service()
        transport = Mock()
        transport.send = AsyncMock()
        service._transport = transport

        with self.assertRaises(InvalidEmailFormatException):
            self._run_async(service.send_verification_code(to_email="bad-email", code="123456"))

        transport.send.assert_not_awaited()

    def test_send_verification_code_invalid_code_raises_and_does_not_send(self) -> None:
        service = self._service()
        transport = Mock()
        transport.send = AsyncMock()
        service._transport = transport

        with self.assertRaises(InvalidVerificationCodeException):
            self._run_async(service.send_verification_code(to_email="test@example.com", code="12ab56"))

        transport.send.assert_not_awaited()

    def test_send_verification_code_invalid_override_from_email_raises(self) -> None:
        service = self._service()
        transport = Mock()
        transport.send = AsyncMock()
        service._transport = transport

        with self.assertRaises(InvalidEmailFormatException):
            self._run_async(
                service.send_verification_code(
                    to_email="test@example.com",
                    code="123456",
                    from_email="bad-email",
                )
            )

        transport.send.assert_not_awaited()
