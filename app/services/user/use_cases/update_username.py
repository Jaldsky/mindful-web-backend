from datetime import datetime, timezone
from typing import NoReturn
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ...auth.exceptions import (
    AuthServiceException,
    UserNotFoundException,
    UsernameAlreadyExistsException,
)
from ...auth.queries import fetch_user_by_username
from ..queries import fetch_user_by_id
from ...types import Username
from .profile import ProfileData
from ....db.models.tables import User


class UpdateUsernameService:
    """Сервис обновления логина текущего пользователя."""

    async def _load_user(self, session: AsyncSession, user_id: UUID) -> User | NoReturn:
        """Приватный метод загрузки пользователя по user_id.

        Args:
            session: Сессия базы данных.
            user_id: Идентификатор пользователя.

        Returns:
            User: Пользователь из БД.

        Raises:
            UserNotFoundException: Если пользователь не найден в системе.
        """
        user = await fetch_user_by_id(session, user_id)
        if not user:
            raise UserNotFoundException("user.errors.user_not_found")
        return user

    async def _ensure_username_available(
        self, session: AsyncSession, username: Username, user_id: UUID
    ) -> None | NoReturn:
        """Приватный метод проверки уникальности логина.

        Args:
            session: Сессия базы данных.
            username: Новый логин.
            user_id: ID текущего пользователя.

        Raises:
            UsernameAlreadyExistsException: Если логин уже занят другим пользователем.
        """
        existing = await fetch_user_by_username(session, username)
        if existing and existing.id != user_id:
            raise UsernameAlreadyExistsException("user.errors.username_exists")

    def _apply_username_update(self, user: User, username: Username) -> bool:
        """Приватный метод обновления логина пользователя.

        Args:
            user: Объект пользователя из БД.
            username: Новый логин.

        Returns:
            bool: True, если логин был изменён.
        """
        if user.username == username:
            return False
        user.username = username
        user.updated_at = datetime.now(timezone.utc)
        return True

    async def exec(
        self,
        session: AsyncSession,
        user_id: UUID,
        username: Username,
    ) -> ProfileData | NoReturn:
        """Метод обновления логина пользователя.

        Процесс включает:
        1. Получение пользователя по user_id
        2. Проверку уникальности нового username
        3. Обновление нового username
        4. Коммит транзакции

        Args:
            session: Сессия базы данных.
            user_id: Идентификатор пользователя.
            username: Новый логин.

        Returns:
            ProfileData: Обновлённые данные профиля пользователя.

        Raises:
            UserNotFoundException: Если пользователь не найден в системе (401).
            UsernameAlreadyExistsException: Если логин уже занят (409).
            AuthServiceException: При неожиданной ошибке.
        """
        try:
            user = await self._load_user(session, user_id)
            await self._ensure_username_available(session, username, user.id)
            is_updated = self._apply_username_update(user, username)
            if is_updated:
                await session.commit()

            return ProfileData(
                username=user.username,
                email=user.email,
            )
        except (UserNotFoundException, UsernameAlreadyExistsException):
            await session.rollback()
            raise
        except Exception:
            await session.rollback()
            raise AuthServiceException("user.errors.auth_service_error")
