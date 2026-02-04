import logging
from typing import NoReturn
from uuid import UUID

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ...types import ActorType
from ....schemas.events.save.request_schema import SaveEventData
from ..exceptions import (
    AnonEventsLimitExceededException,
    DataIntegrityViolationException,
    EventsInsertFailedException,
    TransactionFailedException,
    UnexpectedEventsException,
    UserCreationFailedException,
)
from ..queries import (
    bulk_insert_attention_events,
    count_attention_events_by_user_id,
    insert_user_if_not_exists,
)

logger = logging.getLogger(__name__)


class SaveEventsService:
    """Сервис сохранения событий."""

    async def _ensure_user_exists(self, session: AsyncSession, user_id: UUID) -> None | NoReturn:
        """Приватный метод получения или создания пользователя в базе данных.

        Args:
            session: Сессия базы данных.
            user_id: Идентификатор пользователя.

        Raises:
            UserCreationFailedException: При ошибке создания/получения пользователя.
        """
        try:
            await insert_user_if_not_exists(session, user_id)
        except Exception:
            raise UserCreationFailedException(
                key="events.messages.get_or_create_user_error",
                fallback=f"Unable to create/find user {user_id}!",
                translation_params={"user_id": str(user_id)},
            )

    async def _insert_events(
        self,
        session: AsyncSession,
        data: list[SaveEventData],
        user_id: UUID,
    ) -> None | NoReturn:
        """Приватный метод добавления событий в базу данных.

        Args:
            session: Сессия базы данных.
            data: Данные с событиями.
            user_id: Идентификатор пользователя.

        Raises:
            EventsInsertFailedException: При ошибке подготовки данных для bulk-insert.
        """
        try:
            values = [
                {
                    "user_id": user_id,
                    "domain": event.domain,
                    "event_type": event.event,
                    "timestamp": event.timestamp,
                }
                for event in data
            ]
        except Exception:
            raise EventsInsertFailedException(
                key="events.messages.add_events_error",
                fallback="Failed to insert event into the events table!",
            )

        await bulk_insert_attention_events(session, values)

    async def _enforce_anon_limit(
        self,
        session: AsyncSession,
        data: list[SaveEventData],
        user_id: UUID,
        actor_type: ActorType,
    ) -> None | NoReturn:
        """Приватный метод проверки лимита событий для анонимной сессии.

        Args:
            session: Сессия базы данных.
            data: Данные с событиями.
            user_id: Идентификатор пользователя.
            actor_type: Тип субъекта (access или anon).

        Raises:
            AnonEventsLimitExceededException: При превышении лимита событий для анонима.
        """
        if actor_type != "anon":
            return

        existing_count = await count_attention_events_by_user_id(session, user_id)
        total_count = existing_count + len(data)
        if total_count > 100:
            raise AnonEventsLimitExceededException(
                key="events.errors.anon_events_limit_exceeded",
                fallback="Anonymous events limit exceeded",
            )

    async def exec(
        self,
        session: AsyncSession,
        data: list[SaveEventData],
        user_id: UUID,
        actor_type: ActorType = "access",
    ) -> None | NoReturn:
        """Метод сохранения событий в базе данных.

        Процесс сохранения включает:
        1. Проверку лимита событий для анонимной сессии
        2. Получение или создание пользователя
        3. Подготовку событий для вставки
        4. Коммит транзакции

        Args:
            session: Сессия базы данных.
            data: Данные событий для сохранения.
            user_id: Идентификатор пользователя.
            actor_type: Тип субъекта (access или anon).

        Raises:
            AnonEventsLimitExceededException: При превышении лимита событий для анонима.
            UserCreationFailedException: При ошибке создания/получения пользователя.
            EventsInsertFailedException: При ошибке вставки событий.
            DataIntegrityViolationException: При нарушении целостности данных.
            TransactionFailedException: При ошибке транзакции базы данных.
            UnexpectedEventsException: При неожиданной ошибке.
        """
        try:
            await self._enforce_anon_limit(session, data, user_id, actor_type)
            await self._ensure_user_exists(session, user_id)
            await self._insert_events(session, data, user_id)
            await session.commit()

            logger.info(f"Successfully added events for user {user_id}")

        except (
            AnonEventsLimitExceededException,
            UserCreationFailedException,
            EventsInsertFailedException,
        ):
            await session.rollback()
            raise
        except IntegrityError:
            await session.rollback()
            raise DataIntegrityViolationException(
                key="events.messages.data_integrity_error",
                fallback="Data integrity issue when saving events!",
            )
        except SQLAlchemyError:
            await session.rollback()
            raise TransactionFailedException(
                key="events.messages.data_save_error",
                fallback="Database error while saving events!",
            )
        except Exception:
            await session.rollback()
            raise UnexpectedEventsException(
                key="events.messages.unexpected_error",
                fallback="An unexpected error occurred while processing events!",
            )
