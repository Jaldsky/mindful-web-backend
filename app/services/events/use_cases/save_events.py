import logging
from dataclasses import dataclass
from typing import Any, NoReturn
from uuid import UUID

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ....schemas.events.save.request_schema import SaveEventData
from ..exceptions import (
    DataIntegrityViolationException,
    EventsInsertFailedException,
    EventsServiceMessages,
    TransactionFailedException,
    UnexpectedEventsException,
    UserCreationFailedException,
)
from ..queries import bulk_insert_attention_events, insert_user_if_not_exists

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class SaveEventsData:
    """Данные для сохранения событий."""

    data: list[SaveEventData]
    user_id: UUID


class SaveEventsServiceBase:
    """Базовый класс для сервиса сохранения событий."""

    messages: type[EventsServiceMessages] = EventsServiceMessages
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
            raise UserCreationFailedException(self.messages.GET_OR_CREATE_USER_ERROR.format(user_id=user_id))

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
            raise EventsInsertFailedException(self.messages.ADD_EVENTS_ERROR)

        await bulk_insert_attention_events(self.session, values)

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
            async with self.session.begin():
                await self._ensure_user_exists(self.user_id)
                await self._insert_events(self.data, self.user_id)

            logger.info(f"Successfully added events for user {self.user_id}")

        except (UserCreationFailedException, EventsInsertFailedException):
            raise
        except IntegrityError:
            raise DataIntegrityViolationException(self.messages.DATA_INTEGRITY_ERROR)
        except SQLAlchemyError:
            raise TransactionFailedException(self.messages.DATA_SAVE_ERROR)
        except Exception:
            raise UnexpectedEventsException(self.messages.UNEXPECTED_ERROR)
