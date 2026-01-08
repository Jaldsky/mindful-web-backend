from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, NoReturn

from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound, select_autoescape

from .exceptions import EmailSendFailedException
from .types import TemplateName
from .validators import TemplateRendererSettingsValidator


@dataclass(slots=True, frozen=True)
class TemplateRendererSettings:
    """Настройки рендерера шаблонов."""

    templates_dir: Path

    def __post_init__(self) -> None:
        """Магический метод пост-инициализации dataclass."""
        self.validate()

    def validate(self) -> None | NoReturn:
        """Метод валидации настроек рендерера шаблонов.

        Raises:
            InvalidSMTPConfigException: При невалидном пути к директории шаблонов.
        """
        TemplateRendererSettingsValidator.validate(self)


class TemplateRenderer:
    """Jinja2 renderer с ленивой инициализацией и кэшем шаблонов."""

    def __init__(self, settings: TemplateRendererSettings) -> None:
        """Магический метод инициализации рендерера шаблонов.

        Args:
            settings: Настройки рендерера шаблонов.
        """
        self._settings = settings
        self._env: Environment | None = None
        self._cache: dict[str, Template] = {}

    @property
    def env(self) -> Environment:
        """Свойство ленивой инициализации окружения Jinja2.

        Returns:
            Настроенное окружение Jinja2 для рендеринга шаблонов.
        """
        if self._env is None:
            self._env = Environment(
                loader=FileSystemLoader(str(self._settings.templates_dir)),
                autoescape=select_autoescape(["html", "xml"]),
            )
        return self._env

    def render(self, template_name: TemplateName, context: Mapping[str, Any]) -> str:
        """Метод рендеринга шаблона Jinja2.

        Args:
            template_name: Имя шаблона для рендеринга.
            context: Переменные для передачи в шаблон.

        Returns:
            HTML контент.

        Raises:
            EmailSendFailedException: При отсутствии шаблона или ошибке рендеринга.
        """
        try:
            template = self._cache.get(template_name)
            if template is None:
                template = self.env.get_template(template_name)
                self._cache[template_name] = template
            return template.render(**dict(context))
        except TemplateNotFound as e:
            raise EmailSendFailedException(f"Email template '{template_name}' not found") from e
        except Exception as e:
            raise EmailSendFailedException("Failed to render email template") from e
