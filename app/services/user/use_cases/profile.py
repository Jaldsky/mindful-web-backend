from dataclasses import dataclass
from typing import NoReturn
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ...auth.exceptions import UserNotFoundException
from ..queries import fetch_user_by_id
from ...types import Email, Username


@dataclass(slots=True, frozen=True)
class ProfileData:
    """Данные профиля пользователя."""

    username: Username | None
    email: Email | None


class ProfileService:
    """Сервис получения профиля текущего пользователя."""

    async def exec(self, session: AsyncSession, user_id: UUID) -> ProfileData | NoReturn:
        """Метод получения профиля пользователя.

        Процесс включает:
        1. Получение пользователя из БД по user_id
        2. Возврат доменных данных

        Args:
            session: Сессия базы данных.
            user_id: Идентификатор пользователя.

        Returns:
            ProfileData: Данные профиля пользователя.

        Raises:
            UserNotFoundException: Если пользователь не найден в системе (401).
        """
        user = await fetch_user_by_id(session, user_id)
        if not user:
            raise UserNotFoundException(
                key="user.errors.user_not_found",
                fallback="User not found",
            )

        return ProfileData(
            username=user.username,
            email=user.email,
        )
