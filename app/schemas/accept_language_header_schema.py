from typing import Any
from pydantic import BaseModel, field_validator, Field

from ..config import DEFAULT_LOCALE, SUPPORTED_LOCALES
from ..exceptions import UnsupportedLocaleException


class AcceptLanguageHeaderSchema(BaseModel):
    """Схема для значения заголовка Accept-Language."""

    accept_language: str = Field(DEFAULT_LOCALE, description="Тег локали")

    @field_validator("accept_language", mode="before")
    @classmethod
    def normalize_locale(cls, v: Any) -> str:
        """Нормализация тега локали."""
        if v is None or (isinstance(v, str) and not v.strip()):
            return DEFAULT_LOCALE
        raw: str = v.strip() if isinstance(v, str) else str(v).strip()
        return raw.split("-")[0].lower()

    @field_validator("accept_language", mode="after")
    @classmethod
    def validate_locale(cls, v: str) -> str:
        """Валидация тега локали."""
        if v in SUPPORTED_LOCALES:
            return v
        supported_str = ", ".join(SUPPORTED_LOCALES)
        raise UnsupportedLocaleException(
            "general.unsupported_locale",
            translation_params={"supported": supported_str},
        )
