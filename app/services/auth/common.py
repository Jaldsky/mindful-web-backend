import secrets
import bcrypt
from datetime import datetime, timezone
from datetime import timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from ..types import Email
from ..types import VerificationCode
from .types import AccessToken, Password, PasswordHash, RefreshToken, TokenPayload
from .exceptions import (
    AuthMessages,
    EmailAlreadyVerifiedException,
    TokenExpiredException,
    TokenInvalidException,
    UserNotFoundException,
)
from .normalizers import AuthServiceNormalizers
from .queries import fetch_user_by_email
from ...db.models.tables import User
from ...config import JWT_ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, JWT_REFRESH_TOKEN_EXPIRE_DAYS, JWT_SECRET_KEY


def generate_verification_code(length: int = 6) -> VerificationCode:
    """Функция генерации случайного кода подтверждения.

    Args:
        length: Длина кода.

    Returns:
        Случайный код подтверждения из цифр.
    """
    return "".join(secrets.choice("0123456789") for _ in range(length))


def hash_password(password: Password, rounds: int = 12) -> PasswordHash:
    """Функция хеширования пароля с помощью bcrypt.

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


def verify_password(password: Password, password_hash: PasswordHash) -> bool:
    """Функция проверки пароля по bcrypt-хэшу.

    Args:
        password: Пароль в открытом виде.
        password_hash: bcrypt-хэш пароля из БД.

    Returns:
        True, если пароль соответствует хэшу.
    """
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def to_utc_datetime(dt: datetime) -> datetime:
    """Функция нормализации datetime к UTC.

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
        Пользователь с неподтверждённым email.

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


def create_tokens(user_id: UUID) -> tuple[AccessToken, RefreshToken]:
    """Функция создание пары JWT токена доступа и токена обновления.

    Args:
        user_id: UUID пользователя.

    Returns:
        Кортеж с JWT токеном доступа и токеном обновления.
    """
    now = datetime.now(timezone.utc)
    access_payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": "access",
        "jti": uuid4().hex,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
    }
    refresh_payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": uuid4().hex,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)).timestamp()),
    }

    access_token: AccessToken = jwt.encode(access_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    refresh_token: RefreshToken = jwt.encode(refresh_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return access_token, refresh_token


def decode_token(token: AccessToken | RefreshToken) -> TokenPayload:
    """Функция декодирования JWT токена.

    Args:
        token: JWT токен доступа или обновления.

    Returns:
        Payload токена.

    Raises:
        TokenExpiredException: Если токен истёк.
        TokenInvalidException: Если токен невалидный.
    """
    token = AuthServiceNormalizers.normalize_jwt_token(token)
    try:
        payload: TokenPayload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise TokenExpiredException(AuthMessages.TOKEN_EXPIRED)
    except JWTError:
        raise TokenInvalidException(AuthMessages.TOKEN_INVALID)
