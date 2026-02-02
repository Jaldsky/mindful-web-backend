"""Локализатор: загрузка переводов из JSON, хранилище по локалям, получение строк по ключу."""

import json
from pathlib import Path
from typing import Any, cast

from fastapi import Request

from ..config import DEFAULT_LOCALE

Locale = str
LocalizerKey = str
LocalizerDict = dict[str, dict]
LocalizerParams = dict[str, str | int]


def load_translations() -> LocalizerDict:
    """Загружает переводы из папки app/locales.

    Returns:
        Словарь локализации.
    """
    app_dir: Path = Path(__file__).resolve().parent.parent
    locales_dir: Path = app_dir / "locales"
    result: LocalizerDict = {}

    for path in locales_dir.glob("*.json"):
        locale: Locale = path.stem
        with open(path, encoding="utf-8") as f:
            result[locale] = cast(dict, json.load(f))

    return result


class LocalizerStore:
    """Класс с хранилищем переводов в памяти."""

    _translations: LocalizerDict

    def __init__(self, translations: LocalizerDict) -> None:
        """Инициализирует хранилище словарём переводов по локалям.

        Args:
            translations: Словарь локализации.
        """
        self._translations = translations

    def _resolve_locale_dict(self, locale: Locale) -> dict[str, Any] | None:
        """Приватный метод возврата словаря переводов для локали с fallback на DEFAULT_LOCALE.

        Args:
            locale: Тег локали.

        Returns:
            Вложенный словарь переводов или None при пустом хранилище.
        """
        effective: Locale = locale if locale in self._translations else DEFAULT_LOCALE
        return self._translations.get(effective)

    def _get_by_path(self, node: dict[str, Any], parts: list[str]) -> str | None:
        """Приватный метод получения значения по пути из частей ключа.

        Например, key.path.to -> node["key"]["path"]["to"]

        Args:
            node: Корневой словарь.
            parts: Части ключа после разбиения по точке.

        Returns:
            Строка перевода или None при отсутствии или неверном типе.
        """
        try:
            current: Any = node
            for part in parts:
                current = current[part]
            return current if isinstance(current, str) else None
        except (KeyError, TypeError):
            return None

    def get(
        self,
        key: LocalizerKey,
        locale: Locale | None = None,
        **params: str | int,
    ) -> str:
        """Метод возврата перевода по ключу в формате CLASS.PRODUCT.TYPE.TEXT.

        При неизвестной локали используется DEFAULT_LOCALE.
        При отсутствии ключа возвращается сам ключ.
        Поддерживается подстановка параметров в строку ({name}).

        Args:
            key: Ключ вида PRODUCT.TYPE.TEXT.
            locale: Тег локали.
            **params: Параметры для подстановки в строку.

        Returns:
            Строка перевода или ключ при отсутствии перевода.
        """
        loc: Locale = locale or DEFAULT_LOCALE
        locale_dict: dict[str, Any] | None = self._resolve_locale_dict(loc)
        if locale_dict is None:
            return key

        parts: list[str] = key.split(".")
        text: str | None = self._get_by_path(locale_dict, parts)
        if text is None and loc != DEFAULT_LOCALE:
            return self.get(key, DEFAULT_LOCALE, **params)
        if text is None:
            return key

        if params:
            try:
                return text.format(**params)
            except KeyError:
                return text
        return text


class Localizer:
    """Класс локализации."""

    _store: LocalizerStore

    def __init__(self, translations: LocalizerDict | None = None) -> None:
        """Инициализирует локализатора.

        Args:
            translations: Словарь переводов по локалям.
        """
        if translations is None:
            translations = load_translations()
        self._store = LocalizerStore(translations)

    def get(
        self,
        key: str,
        locale: str | None = None,
        **params: str | int,
    ) -> str:
        """Метод получения перевода по ключу и локали.

        Args:
            key: Ключ перевода.
            locale: Тег локали.
            **params: Параметры для подстановки в строку.

        Returns:
            Строка перевода или ключ при отсутствии перевода.
        """
        return self._store.get(key, locale=locale, **params)


def localize_key(request: Request, key: str, fallback: str, **params: str | int) -> str:
    """Функция локализации по ключу.

    Если локализатора нет или ключ не найден, то возвращает fallback.
    Параметры подставляются в строку перевода {name}.

    Args:
        request: HTTP-запрос.
        key: Ключ перевода.
        fallback: Строка по умолчанию при отсутствии локализатора или ключа.
        **params: Плейсхолдеры для подстановки в строку.

    Returns:
        Переведённая строка или fallback.
    """
    localizer: Localizer | None = getattr(request.app.state, "localizer", None)
    if not localizer:
        return fallback

    locale: str = getattr(request.state, "locale", "en")
    translated: str = localizer.get(key, locale=locale, **params)
    if translated == key or not isinstance(translated, str):
        return fallback

    return translated
