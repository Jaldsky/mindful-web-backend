import logging
from dataclasses import dataclass
from typing import Any

from datetime import datetime, timedelta, timezone
from email_validator import validate_email, EmailNotValidError
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import VERIFICATION_CODE_EXPIRE_MINUTES
from .common import generate_verification_code, hash_password
from .constants import (
    MAX_PASSWORD_LENGTH,
    MAX_USERNAME_LENGTH,
    MIN_PASSWORD_LENGTH,
    MIN_USERNAME_LENGTH,
)
from ...db.models.tables import User, VerificationCode as VerificationCodeModel
from ...services.email import EmailService
from .exceptions import (
    AuthMessages,
    AuthServiceException,
    EmailAlreadyExistsException,
    EmailSendFailedException,
    InvalidEmailFormatException,
    InvalidPasswordFormatException,
    InvalidUsernameFormatException,
    UsernameAlreadyExistsException,
)
from ..types import Email, UserId, VerificationCode
from .types import Password, PasswordHash, Username

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RegisterData:
    """Данные для регистрации пользователя."""

    username: Username
    email: Email
    password: Password


class RegisterServiceBase(RegisterData):
    """Базовый класс для сервиса регистрации."""

    messages: type[AuthMessages] = AuthMessages
    session: AsyncSession

    def __init__(self, session: AsyncSession, **kwargs: Any) -> None:
        """Магический метод инициализации базового класса регистрации.

        Args:
            session: Сессия базы данных.
            **kwargs: Аргументы для RegisterData.
        """
        super().__init__(**kwargs)
        self.session = session

    def normalize(self) -> None:
        """Метод нормализации входных данных."""
        self.username = self._normalize_username(self.username)
        self.email = self._normalize_email(self.email)
        self.password = self._normalize_password(self.password)

    def _normalize_username(self, username: Username) -> Username:
        """Приватный метод нормализации имени пользователя.

        Args:
            username: Имя пользователя для нормализации.

        Returns:
            Нормализованный username.
        """
        return (username or "").strip().lower()

    def _normalize_email(self, email: Email) -> Email:
        """Приватный метод нормализации электронной почты.

        Args:
            email: Электронная почта для нормализации.

        Returns:
            Нормализованный email.
        """
        return (email or "").strip().lower()

    def _normalize_password(self, password: Password) -> Password:
        """Приватный метод нормализации пользовательского пароля.

        Args:
            password: Пароль для нормализации.

        Returns:
            Пароль или пустая строка, если None.
        """
        return password or ""

    def validate(self) -> None:
        """Метод валидации всех входных данных."""
        self._validate_username(self.username)
        self._validate_email(self.email)
        self._validate_password(self.password)

    def _validate_email(self, email: Email) -> None:
        """Приватный метод валидации формата электронной почты.

        Args:
            email: Email адрес для валидации.

        Raises:
            InvalidEmailFormatException: Если email имеет неверный формат или пустой.
        """
        if not email or not email.strip():
            raise InvalidEmailFormatException("Email cannot be empty")

        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError:
            raise InvalidEmailFormatException("Invalid email format")

    def _validate_username(self, username: Username) -> None:
        """Приватный метод валидации формата имени пользователя.

        Args:
            username: Имя пользователя для валидации.

        Raises:
            InvalidUsernameFormatException: Если username не соответствует требованиям.
        """
        if len(username) < MIN_USERNAME_LENGTH or len(username) > MAX_USERNAME_LENGTH:
            raise InvalidUsernameFormatException(
                f"Username must be {MIN_USERNAME_LENGTH}-{MAX_USERNAME_LENGTH} characters long"
            )
        if not all(ch.islower() or ch.isdigit() or ch == "_" for ch in username):
            raise InvalidUsernameFormatException(
                "Username must contain only lowercase letters, numbers, and underscores"
            )
        if username.startswith("_") or username.endswith("_"):
            raise InvalidUsernameFormatException("Username cannot start or end with underscore")

    def _validate_password(self, password: Password) -> None:
        """Приватный метод валидации формата пользовательского пароля.

        Args:
            password: Пароль для валидации.

        Raises:
            InvalidPasswordFormatException: Если password не соответствует требованиям.
        """
        if len(password) < MIN_PASSWORD_LENGTH or len(password) > MAX_PASSWORD_LENGTH:
            raise InvalidPasswordFormatException(
                f"Password must be {MIN_PASSWORD_LENGTH}-{MAX_PASSWORD_LENGTH} characters long"
            )
        if not any(ch.isalpha() for ch in password):
            raise InvalidPasswordFormatException("Password must contain at least one letter")
        if not any(ch.isdigit() for ch in password):
            raise InvalidPasswordFormatException("Password must contain at least one digit")


class RegisterService(RegisterServiceBase):
    """Сервис регистрации пользователей."""

    def __init__(self, session: AsyncSession, **kwargs: Any) -> None:
        """Магический метод инициализации.

        Args:
            session: Сессия базы данных.
            **kwargs: Аргументы для RegisterData.
        """
        super().__init__(session=session, **kwargs)

    async def _create_verification_code(self, user_id: UserId) -> VerificationCode:
        """Приватный метод создания кода подтверждения для пользователя.

        Args:
            user_id: ID пользователя.

        Returns:
            Сгенерированный код подтверждения.
        """
        code: VerificationCode = generate_verification_code()
        now = datetime.now(timezone.utc)
        expires_at: datetime = now + timedelta(minutes=VERIFICATION_CODE_EXPIRE_MINUTES)
        self.session.add(VerificationCodeModel(user_id=user_id, code=code, expires_at=expires_at, created_at=now))
        return code

    async def _check_uniqueness(self) -> None:
        """Приватный метод проверки уникальности username и email.

        Raises:
            UsernameAlreadyExistsException: Если username уже существует.
            EmailAlreadyExistsException: Если email уже существует.
        """
        result = await self.session.execute(
            select(User).where(
                and_(
                    User.deleted_at.is_(None),
                    or_(User.username == self.username, User.email == self.email),
                )
            )
        )
        existing_users = result.scalars().all()

        for user in existing_users:
            if user.username == self.username:
                raise UsernameAlreadyExistsException(self.messages.USERNAME_EXISTS)
            if user.email == self.email:
                raise EmailAlreadyExistsException(self.messages.EMAIL_EXISTS)

    async def _create_user_with_code(self) -> tuple[User, VerificationCode]:
        """Приватный метод создания пользователя и кода подтверждения.

        Процесс включает:
        1. Хеширование пароля
        2. Создание объекта User
        3. Добавление пользователя в сессию и flush для получения ID
        4. Создание кода подтверждения для пользователя

        Returns:
            Кортеж (User, VerificationCode) с созданным пользователем и кодом подтверждения.
        """
        password: PasswordHash = hash_password(self.password)
        now = datetime.now(timezone.utc)
        user: User = User(
            username=self.username,
            email=self.email,
            password=password,
            is_verified=False,
            created_at=now,
            updated_at=now,
        )
        self.session.add(user)
        await self.session.flush()

        code: VerificationCode = await self._create_verification_code(user.id)
        return user, code

    async def _send_verification_email(self, email: Email, code: VerificationCode) -> None:
        """Приватный метод отправки кода подтверждения на email.

        Args:
            email: Email адрес получателя.
            code: Код подтверждения для отправки.

        Raises:
            EmailSendFailedException: Если не удалось отправить email.
        """
        try:
            await EmailService().send_verification_code(to_email=email, code=code)
        except Exception:
            raise EmailSendFailedException(self.messages.EMAIL_SEND_FAILED)

    async def exec(self) -> User:
        """Метод регистрации пользователя.

        Процесс регистрации включает:
        1. Нормализацию входных данных
        2. Валидацию формата всех полей
        3. Проверку уникальности username и email
        4. Создание пользователя и кода подтверждения
        5. Отправку кода подтверждения на email
        6. Коммит транзакции

        Returns:
            Созданный объект User.

        Raises:
            InvalidUsernameFormatException: При неверном формате username.
            InvalidEmailFormatException: При неверном формате email.
            InvalidPasswordFormatException: При неверном формате password.
            UsernameAlreadyExistsException: Если username уже существует.
            EmailAlreadyExistsException: Если email уже существует.
            EmailSendFailedException: Если не удалось отправить email.
            AuthServiceException: При неожиданной ошибке.
        """
        self.normalize()
        self.validate()

        try:
            await self._check_uniqueness()
            user, code = await self._create_user_with_code()
            await self._send_verification_email(self.email, code)

            await self.session.commit()
            logger.info(f"User registered: {self.username} ({self.email})")
            return user

        except (
            InvalidUsernameFormatException,
            InvalidEmailFormatException,
            InvalidPasswordFormatException,
            UsernameAlreadyExistsException,
            EmailAlreadyExistsException,
            EmailSendFailedException,
        ):
            await self.session.rollback()
            raise
        except Exception:
            await self.session.rollback()
            raise AuthServiceException(self.messages.AUTH_SERVICE_ERROR)
