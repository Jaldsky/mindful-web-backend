import logging
from dataclasses import dataclass
from typing import Any, NoReturn
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


@dataclass(slots=True, frozen=True)
class SaveEventsData:
    """Данные для сохранения событий."""

    data: list[SaveEventData]
    user_id: UUID
    actor_type: ActorType = "access"


class SaveEventsServiceBase:
    """Базовый класс для сервиса сохранения событий."""

    session: AsyncSession
    _data: SaveEventsData

    def __init__(self, session: AsyncSession, **kwargs: Any) -> None:
        """Магический метод инициализации базового класса сохранения событий.

        Args:
            session: Сессия базы данных.
            **kwargs: Аргументы для SaveEventsData.
        """
        self.session = session
        self._data = SaveEventsData(**kwargs)

    @property
    def data(self) -> list[SaveEventData]:
        """Свойство получения данных событий из данных сохранения.

        Returns:
            Список данных событий.
        """
        return self._data.data

    @property
    def user_id(self) -> UUID:
        """Свойство получения user_id из данных сохранения.

        Returns:
            Идентификатор пользователя.
        """
        return self._data.user_id

    @property
    def actor_type(self) -> str:
        """Свойство получения типа субъекта (access/anon).

        Returns:
            Тип access или anon.
        """
        return self._data.actor_type


class SaveEventsService(SaveEventsServiceBase):
    """Сервис сохранения событий."""

    def __init__(self, session: AsyncSession, **kwargs: Any) -> None:
        """Магический метод инициализации.

        Args:
            session: Сессия базы данных.
            **kwargs: Аргументы для SaveEventsData.
        """
        super().__init__(session=session, **kwargs)

    async def _ensure_user_exists(self, user_id: UUID) -> None | NoReturn:
        """Приватный метод получения или создания пользователя в базе данных.

        Args:
            user_id: Идентификатор пользователя.

        Raises:
            UserCreationFailedException: При ошибке создания/получения пользователя.
        """
        try:
            await insert_user_if_not_exists(self.session, user_id)
        except Exception:
            raise UserCreationFailedException(
                "events.messages.get_or_create_user_error",
                translation_params={"user_id": str(user_id)},
            )

    async def _insert_events(self, data: list[SaveEventData], user_id: UUID) -> None | NoReturn:
        """Приватный метод добавления событий в базу данных.

        Args:
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
            raise EventsInsertFailedException("events.messages.add_events_error")

        await bulk_insert_attention_events(self.session, values)

    async def _enforce_anon_limit(self) -> None | NoReturn:
        """Приватный метод проверки лимита событий для анонимной сессии."""
        if self.actor_type != "anon":
            return

        existing_count = await count_attention_events_by_user_id(self.session, self.user_id)
        total_count = existing_count + len(self.data)
        if total_count > 100:
            raise AnonEventsLimitExceededException("events.errors.anon_events_limit_exceeded")

    async def exec(self) -> None | NoReturn:
        """Метод сохранения событий в базе данных.

        Процесс сохранения включает:
        1. Получение или создание пользователя
        2. Подготовку событий для вставки
        3. Коммит транзакции

        Raises:
            UserCreationFailedException: При ошибке создания/получения пользователя.
            EventsInsertFailedException: При ошибке вставки событий.
            DataIntegrityViolationException: При нарушении целостности данных.
            TransactionFailedException: При ошибке транзакции базы данных.
            UnexpectedEventsException: При неожиданной ошибке.
        """
        try:
            await self._enforce_anon_limit()
            await self._ensure_user_exists(self.user_id)
            await self._insert_events(self.data, self.user_id)
            await self.session.commit()

            logger.info(f"Successfully added events for user {self.user_id}")

        except (UserCreationFailedException, EventsInsertFailedException):
            await self.session.rollback()
            raise
        except IntegrityError:
            await self.session.rollback()
            raise DataIntegrityViolationException("events.messages.data_integrity_error")
        except SQLAlchemyError:
            await self.session.rollback()
            raise TransactionFailedException("events.messages.data_save_error")
        except Exception:
            await self.session.rollback()
            raise UnexpectedEventsException("events.messages.unexpected_error")
