import secrets
import bcrypt
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from ..types import Email
from ..types import VerificationCode
from .types import Password, PasswordHash
from .exceptions import AuthMessages, EmailAlreadyVerifiedException, UserNotFoundException
from .queries import fetch_user_by_email
from ...db.models.tables import User


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


def to_utc_datetime(dt: datetime) -> datetime:
    """Нормализация datetime к UTC.

    Args:
        dt: datetime.

    Returns:
        datetime в UTC.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


async def get_unverified_user_by_email(
    session: AsyncSession,
    email: Email,
    messages: type[AuthMessages] = AuthMessages,
) -> User:
    """Функция получения пользователя по email для операций с неподтверждённым email.

    Args:
        session: Сессия базы данных.
        email: Email пользователя.
        messages: Класс сообщений сервиса.

    Returns:
        User: Пользователь с неподтверждённым email.

    Raises:
        UserNotFoundException: Если пользователь не найден.
        EmailAlreadyVerifiedException: Если email уже подтверждён.
    """
    user = await fetch_user_by_email(session, email)
    if not user:
        raise UserNotFoundException(messages.USER_NOT_FOUND)
    if user.is_verified:
        raise EmailAlreadyVerifiedException(messages.EMAIL_ALREADY_VERIFIED)
    return user
