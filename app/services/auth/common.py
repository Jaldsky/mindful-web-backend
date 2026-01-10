import secrets
import bcrypt

from ..types import VerificationCode
from .types import Password, PasswordHash


def generate_verification_code(length: int = 6) -> VerificationCode:
    """Генерация случайного кода подтверждения.

    Args:
        length: Длина кода.

    Returns:
        Случайный код подтверждения из цифр.
    """
    return "".join(secrets.choice("0123456789") for _ in range(length))


def hash_password(password: Password, rounds: int = 12) -> PasswordHash:
    """Хеширование пароля с помощью bcrypt.

    Args:
        password: Пароль для хеширования.
        rounds: Количество прогонов.

    Returns:
        Хеш пароля.
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=rounds)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")
