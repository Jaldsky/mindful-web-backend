from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ...auth.exceptions import AuthMessages, UserNotFoundException
from ..queries import fetch_user_by_id
from ...types import Email, Username


@dataclass(slots=True, frozen=True)
class UserProfile:
    """Входные данные для получения профиля пользователя."""

    user_id: UUID


@dataclass(slots=True, frozen=True)
class ProfileData:
    """Данные профиля пользователя."""

    username: Username | None
    email: Email | None


class ProfileServiceBase:
    """Базовый класс сервиса user profile."""

    session: AsyncSession
    _data: UserProfile

    def __init__(self, session: AsyncSession, **kwargs: Any) -> None:
        """Магический метод инициализации базового класса получения профиля.

        Args:
            session: Сессия базы данных.
            **kwargs: Аргументы для UserProfile.
        """
        self.session = session
        self._data = UserProfile(**kwargs)

    @property
    def user_id(self) -> UUID:
        """Свойство получения user_id из данных профиля.

        Returns:
            ID пользователя.
        """
        return self._data.user_id


class ProfileService(ProfileServiceBase):
    """Сервис получения профиля текущего пользователя."""

    async def exec(self) -> ProfileData:
        """Метод получения профиля пользователя.

        Процесс включает:
        1. Получение пользователя из БД по user_id
        2. Возврат доменных данных

        Returns:
            ProfileData: Данные профиля пользователя.

        Raises:
            UserNotFoundException: Если пользователь не найден в системе (401).
        """
        user = await fetch_user_by_id(self.session, self.user_id)
        if not user:
            raise UserNotFoundException(AuthMessages.USER_NOT_FOUND)

        return ProfileData(
            username=user.username,
            email=user.email,
        )
