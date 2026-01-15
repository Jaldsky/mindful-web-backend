from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, NoReturn
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ...auth.common import generate_verification_code
from ...auth.exceptions import (
    AuthMessages,
    AuthServiceException,
    EmailAlreadyExistsException,
    EmailSendFailedException,
    UserNotFoundException,
)
from ...auth.queries import fetch_user_by_email_or_pending
from ..queries import fetch_user_by_id
from ...types import Email, VerificationCode, UserId
from ....config import VERIFICATION_CODE_EXPIRE_MINUTES
from ....db.models.tables import VerificationCode as VerificationCodeModel
from ....db.models.tables import User
from ....services.email import EmailService
from .profile import ProfileData


@dataclass(slots=True, frozen=True)
class UpdateEmail:
    """Данные для обновления email пользователя."""

    user_id: UUID
    email: Email


class UpdateEmailServiceBase:
    """Базовый класс для сервиса обновления email пользователя."""

    messages: type[AuthMessages] = AuthMessages
    session: AsyncSession
    _data: UpdateEmail

    def __init__(self, session: AsyncSession, **kwargs: Any) -> None:
        """Магический метод инициализации базового класса.

        Args:
            session: Сессия базы данных.
            **kwargs: Аргументы для UpdateEmail.
        """
        self.session = session
        self._data = UpdateEmail(**kwargs)

    @property
    def user_id(self) -> UUID:
        """Свойство получения user_id из данных запроса.

        Returns:
            UUID: Идентификатор пользователя.
        """
        return self._data.user_id

    @property
    def email(self) -> Email:
        """Свойство получения email из данных запроса.

        Returns:
            Email: Email пользователя.
        """
        return self._data.email


class UpdateEmailService(UpdateEmailServiceBase):
    """Сервис обновления email текущего пользователя."""

    async def _load_user(self) -> User:
        """Приватный метод загрузки пользователя по user_id.

        Returns:
            User: Пользователь из БД.

        Raises:
            UserNotFoundException: Если пользователь не найден в системе.
        """
        user = await fetch_user_by_id(self.session, self.user_id)
        if not user:
            raise UserNotFoundException(self.messages.USER_NOT_FOUND)
        return user

    async def _ensure_email_available(self, user_id: UserId) -> None | NoReturn:
        """Приватный метод проверки уникальности email.

        Args:
            user_id: ID текущего пользователя.

        Raises:
            EmailAlreadyExistsException: Если email уже занят другим пользователем.
        """
        existing = await fetch_user_by_email_or_pending(self.session, self.email)
        if existing and existing.id != user_id:
            raise EmailAlreadyExistsException(self.messages.EMAIL_EXISTS)

    def _is_email_update_required(self, user: User) -> bool:
        """Приватный метод проверки необходимости обновления email.

        Args:
            user: Объект пользователя из БД.

        Returns:
            bool: True, если email нужно обновить или переподтвердить.
        """
        if user.email == self.email and user.is_verified:
            return False
        return True

    def _apply_email_update(self, user: User) -> User:
        """Приватный метод обновления email пользователя.

        Args:
            user: Объект пользователя из БД.

        Returns:
            User: Обновлённый объект пользователя.
        """
        now = datetime.now(timezone.utc)
        user.pending_email = self.email
        user.updated_at = now
        return user

    async def _create_verification_code(self, user_id: UserId) -> VerificationCode:
        """Приватный метод создания кода подтверждения для пользователя.

        Args:
            user_id: ID пользователя.

        Returns:
            VerificationCode: Сгенерированный код подтверждения.
        """
        code: VerificationCode = generate_verification_code()
        now = datetime.now(timezone.utc)
        expires_at: datetime = now + timedelta(minutes=VERIFICATION_CODE_EXPIRE_MINUTES)
        self.session.add(VerificationCodeModel(user_id=user_id, code=code, expires_at=expires_at, created_at=now))
        return code

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

    async def exec(self) -> ProfileData | NoReturn:
        """Метод обновления email пользователя.

        Процесс включает:
        1. Получение пользователя по user_id
        2. Проверку уникальности email
        3. Сохранение pending_email для подтверждения
        4. Создание кода подтверждения
        5. Отправку письма с кодом
        6. Коммит транзакции

        Returns:
            ProfileData: Обновлённые данные профиля пользователя.

        Raises:
            UserNotFoundException: Если пользователь не найден в системе (401).
            EmailAlreadyExistsException: Если email уже занят (409).
            EmailSendFailedException: Если не удалось отправить email (500).
            AuthServiceException: При неожиданной ошибке.
        """
        try:
            user = await self._load_user()
            await self._ensure_email_available(user.id)
            if not self._is_email_update_required(user):
                return ProfileData(
                    username=user.username,
                    email=user.email,
                )
            user = self._apply_email_update(user)
            code = await self._create_verification_code(user.id)
            await self._send_verification_email(self.email, code)

            await self.session.commit()

            return ProfileData(
                username=user.username,
                email=user.email,
            )
        except (UserNotFoundException, EmailAlreadyExistsException, EmailSendFailedException):
            await self.session.rollback()
            raise
        except Exception:
            await self.session.rollback()
            raise AuthServiceException(self.messages.AUTH_SERVICE_ERROR)
