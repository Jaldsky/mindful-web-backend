from __future__ import annotations
import logging
from typing import NoReturn, TYPE_CHECKING
from abc import ABC, abstractmethod
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from .exceptions import (
    DataIntegrityViolationException,
    EventsInsertFailedException,
    EventsServiceException,
    EventsServiceMessages,
    TransactionFailedException,
    UnexpectedEventsException,
    UserCreationFailedException,
)
from ...db.models.tables import AttentionEvent, User
from ...schemas.events import SendEventData

logger = logging.getLogger(__name__)


class SendEventsServiceBase(ABC):
    """Базовый класс сервиса событий."""

    exception = EventsServiceException
    messages = EventsServiceMessages

    def __init__(self, session: AsyncSession) -> None:
        """Инициализация класса.

        Args:
            session: Сессия с базой данных.
        """
        self.session = session

    @abstractmethod
    async def exec(self, *args, **kwargs):
        """Метод выполнения основной логики."""


class SendEventsService(SendEventsServiceBase):
    """Класс сервиса событий."""

    async def _ensure_user_exists(self, user_id: UUID) -> None | NoReturn:
        """Метод получение или создание пользователя в базе данных.

        Args:
            user_id: Идентификатор пользователя.

        Raises:
            UserCreationFailedException: При ошибке создания/получения пользователя.
        """
        try:
            user_insert = insert(User).values(id=user_id).on_conflict_do_nothing(index_elements=["id"])
            await self.session.execute(user_insert)
        except Exception as e:
            logger.error(f"Failed to ensure user {user_id} exists: {e.__str__()}")
            raise UserCreationFailedException(self.messages.GET_OR_CREATE_USER_ERROR.format(user_id=user_id))

    async def _insert_events(self, data: list[SendEventData], user_id: UUID) -> None | NoReturn:
        """Метод добавления событий в базу данных.

        Args:
            data: Данные с событиями.
            user_id: Идентификатор пользователя.

        Raises:
            EventsInsertFailedException: При ошибке подготовки событий для вставки.
        """
        try:
            events = [
                AttentionEvent(
                    user_id=user_id,
                    domain=event.domain,
                    event_type=event.event,
                    timestamp=event.timestamp,
                )
                for event in data
            ]
            for event in events:
                self.session.add(event)
        except Exception as e:
            logger.error(f"Failed to prepare events for user {user_id}: {e}")
            raise EventsInsertFailedException(self.messages.ADD_EVENTS_ERROR)

    async def create_events(self, data: list[SendEventData], user_id: UUID) -> None | NoReturn:
        """Метод создания событий в базе данных.

        Args:
            data: Данные с событиями.
            user_id: Идентификатор пользователя.

        Raises:
            UserCreationFailedException: При ошибке создания/получения пользователя.
            EventsInsertFailedException: При ошибке вставки событий.
            DataIntegrityViolationException: При нарушении целостности данных.
            TransactionFailedException: При ошибке транзакции базы данных.
            UnexpectedEventsException: При неожиданной ошибке.
        """
        try:
            await self._ensure_user_exists(user_id)
            await self._insert_events(data, user_id)
            await self.session.commit()
            logger.info(f"Successfully processed {len(data)} events for user {user_id}")
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Integrity error while processing events for user {user_id}: {e}")
            raise DataIntegrityViolationException(self.messages.DATA_INTEGRITY_ERROR)
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Database error while processing events for user {user_id}: {e}")
            raise TransactionFailedException(self.messages.DATA_SAVE_ERROR)
        except EventsServiceException:
            await self.session.rollback()
            raise
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Unexpected error while processing events for user {user_id}: {e}")
            raise UnexpectedEventsException(self.messages.UNEXPECTED_ERROR)

    async def exec(self, data: list[SendEventData], user_id: UUID) -> None:
        """Метод выполнения основной логики.

        Args:
            data: Данные с событиями.
            user_id: Идентификатор пользователя.
        """
        await self.create_events(data, user_id)
