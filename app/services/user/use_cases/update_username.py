from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, NoReturn
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ...auth.exceptions import (
    AuthMessages,
    AuthServiceException,
    UserNotFoundException,
    UsernameAlreadyExistsException,
)
from ...auth.queries import fetch_user_by_username
from ..queries import fetch_user_by_id
from ...types import Username
from .profile import ProfileData
from ....db.models.tables import User


@dataclass(slots=True, frozen=True)
class UpdateUsername:
    """Данные для обновления логина пользователя."""

    user_id: UUID
    username: Username


class UpdateUsernameServiceBase:
    """Базовый класс для сервиса обновления логина пользователя."""

    messages: type[AuthMessages] = AuthMessages
    session: AsyncSession
    _data: UpdateUsername

    def __init__(self, session: AsyncSession, **kwargs: Any) -> None:
        """Магический метод инициализации базового класса.

        Args:
            session: Сессия базы данных.
            **kwargs: Аргументы для UpdateUsername.
        """
        self.session = session
        self._data = UpdateUsername(**kwargs)

    @property
    def user_id(self) -> UUID:
        """Свойство получения user_id из данных запроса.

        Returns:
            UUID: Идентификатор пользователя.
        """
        return self._data.user_id

    @property
    def username(self) -> Username:
        """Свойство получения username из данных запроса.

        Returns:
            Username: Логин пользователя.
        """
        return self._data.username


class UpdateUsernameService(UpdateUsernameServiceBase):
    """Сервис обновления логина текущего пользователя."""

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

    async def _ensure_username_available(self, user_id: UUID) -> None | NoReturn:
        """Приватный метод проверки уникальности логина.

        Args:
            user_id: ID текущего пользователя.

        Raises:
            UsernameAlreadyExistsException: Если логин уже занят другим пользователем.
        """
        existing = await fetch_user_by_username(self.session, self.username)
        if existing and existing.id != user_id:
            raise UsernameAlreadyExistsException(self.messages.USERNAME_EXISTS)

    def _apply_username_update(self, user: User) -> bool:
        """Приватный метод обновления логина пользователя.

        Args:
            user: Объект пользователя из БД.

        Returns:
            bool: True, если логин был изменён.
        """
        if user.username == self.username:
            return False
        user.username = self.username
        user.updated_at = datetime.now(timezone.utc)
        return True

    async def exec(self) -> ProfileData | NoReturn:
        """Метод обновления логина пользователя.

        Процесс включает:
        1. Получение пользователя по user_id
        2. Проверку уникальности нового username
        3. Обновление нового username
        4. Коммит транзакции

        Returns:
            ProfileData: Обновлённые данные профиля пользователя.

        Raises:
            UserNotFoundException: Если пользователь не найден в системе (401).
            UsernameAlreadyExistsException: Если логин уже занят (409).
            AuthServiceException: При неожиданной ошибке.
        """
        try:
            user = await self._load_user()
            await self._ensure_username_available(user.id)
            is_updated = self._apply_username_update(user)
            if is_updated:
                await self.session.commit()

            return ProfileData(
                username=user.username,
                email=user.email,
            )
        except (UserNotFoundException, UsernameAlreadyExistsException):
            await self.session.rollback()
            raise
        except Exception:
            await self.session.rollback()
            raise AuthServiceException(self.messages.AUTH_SERVICE_ERROR)
