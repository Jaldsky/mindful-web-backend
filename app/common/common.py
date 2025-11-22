from enum import Enum


class StringEnum(str, Enum):
    """Базовая форма для энумерации."""

    def __str__(self) -> str:
        """Магический метод возвращения строкового представления.

        Returns:
            Строковое представление.
        """
        return str.__str__(self)

    def __iter__(self):
        """Магический метод возвращения итерационного представления.

        Returns:
            Итерационное представление.
        """
        return iter((value.value for value in self))


class FormException(Exception):
    """Базовая форма для исключений."""

    def __init__(self, message: str) -> None:
        """
        Args:
            message: Сообщение об ошибке.
        """
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        """Строковое представление исключения.

        Returns:
            Сообщение исключения.
        """
        return self.message


def read_text_file(file_path: str, encoding: str = "utf-8") -> str:
    """Безопасно читает текстовый файл целиком.

    Args:
        file_path: Абсолютный путь к файлу.
        encoding: Кодировка файла.

    Returns:
        Содержимое файла как строка.
    """
    with open(file_path, "r", encoding=encoding) as f:
        return f.read()
