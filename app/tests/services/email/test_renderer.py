import tempfile
from pathlib import Path
from unittest import TestCase

from app.services.email.exceptions import EmailSendFailedException, InvalidSMTPConfigException
from app.services.email.renderer import TemplateRenderer, TemplateRendererSettings
from app.services.email.smtp import EmailServiceSettings


class TestTemplateRendererSettings(TestCase):
    """Тесты настроек TemplateRendererSettings."""

    def test_templates_dir_valid_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            settings = TemplateRendererSettings(templates_dir=Path(tmp))
            self.assertEqual(settings.templates_dir, Path(tmp))

    def test_templates_dir_not_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            not_exists = Path(tmp).joinpath("missing")
            with self.assertRaises(InvalidSMTPConfigException):
                TemplateRendererSettings(templates_dir=not_exists)

    def test_templates_dir_is_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp).joinpath("file.txt")
            p.write_text("x", encoding="utf-8")
            with self.assertRaises(InvalidSMTPConfigException):
                TemplateRendererSettings(templates_dir=p)


class TestTemplateRenderer(TestCase):
    """Тесты рендеринга TemplateRenderer."""

    def _email_settings(self) -> EmailServiceSettings:
        return EmailServiceSettings(
            host="localhost",
            port=587,
            user=None,
            password=None,
            from_email="noreply@example.com",
            from_name="Mindful",
            timeout=30,
            use_tls=False,
        )

    def test_render_success_with_repo_template(self) -> None:
        email_settings = self._email_settings()
        renderer = TemplateRenderer(TemplateRendererSettings(templates_dir=email_settings.templates_dir))
        html = renderer.render("verification_code.html", context={"code": "123456"})
        self.assertIn("123456", html)

    def test_render_missing_template_raises(self) -> None:
        email_settings = self._email_settings()
        renderer = TemplateRenderer(TemplateRendererSettings(templates_dir=email_settings.templates_dir))
        with self.assertRaises(EmailSendFailedException):
            renderer.render("missing.html", context={})
