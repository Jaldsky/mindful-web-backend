import logging
from dataclasses import dataclass
from typing import Any, NoReturn

from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from ..common import generate_verification_code, hash_password
from ..queries import fetch_users_by_username_or_email
from ..exceptions import (
    AuthMessages,
    AuthServiceException,
    EmailAlreadyExistsException,
    EmailSendFailedException,
    InvalidEmailFormatException,
    InvalidPasswordFormatException,
    InvalidUsernameFormatException,
    UsernameAlreadyExistsException,
)
from ..types import Password, PasswordHash
from ...types import Email, UserId, VerificationCode, Username
from ....db.models.tables import User, VerificationCode as VerificationCodeModel
from ....services.email import EmailService
from ....config import VERIFICATION_CODE_EXPIRE_MINUTES

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class RegisterUser:
    """Данные для регистрации пользователя."""

    username: Username
    email: Email
    password: Password


class RegisterServiceBase:
    """Базовый класс для сервиса регистрации."""

    messages: type[AuthMessages] = AuthMessages
    session: AsyncSession
    _data: RegisterUser

    def __init__(self, session: AsyncSession, **kwargs: Any) -> None:
        """Магический метод инициализации базового класса регистрации.

        Args:
            session: Сессия базы данных.
            **kwargs: Аргументы для RegisterUser.
        """
        self.session = session
        self._data = RegisterUser(**kwargs)

    @property
    def username(self) -> Username:
        """Свойство получения username из данных регистрации.

        Returns:
            Username пользователя.
        """
        return self._data.username

    @property
    def email(self) -> Email:
        """Свойство получения email из данных регистрации.

        Returns:
            Email адрес пользователя.
        """
        return self._data.email

    @property
    def password(self) -> Password:
        """Свойство получения password из данных регистрации.

        Returns:
            Пароль пользователя.
        """
        return self._data.password


class RegisterService(RegisterServiceBase):
    """Сервис регистрации пользователей."""

    def __init__(self, session: AsyncSession, **kwargs: Any) -> None:
        """Магический метод инициализации.

        Args:
            session: Сессия базы данных.
            **kwargs: Аргументы для RegisterUser.
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

    async def _check_uniqueness(self) -> None | NoReturn:
        """Приватный метод проверки уникальности username и email.

        Raises:
            UsernameAlreadyExistsException: Если username уже существует.
            EmailAlreadyExistsException: Если email уже существует.
        """
        existing_users = await fetch_users_by_username_or_email(self.session, self.username, self.email)

        for user in existing_users:
            if user.username == self.username:
                raise UsernameAlreadyExistsException(self.messages.USERNAME_EXISTS)
            if user.email == self.email:
                raise EmailAlreadyExistsException(self.messages.EMAIL_EXISTS)

    async def _create_user(self) -> User:
        """Приватный метод создания пользователя.

        Процесс включает:
        1. Хеширование пароля
        2. Создание объекта User
        3. Добавление пользователя в сессию

        Returns:
            Созданный объект User.
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
        return user

    async def _send_verification_email(self, email: Email, code: VerificationCode) -> None | NoReturn:
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

    async def exec(self) -> User | NoReturn:
        """Метод регистрации пользователя.

        Процесс регистрации включает:
        1. Проверку уникальности username и email
        2. Создание пользователя
        3. Flush для получения ID пользователя
        4. Создание кода подтверждения
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
        try:
            await self._check_uniqueness()
            user = await self._create_user()
            await self.session.flush()
            code = await self._create_verification_code(user.id)
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
