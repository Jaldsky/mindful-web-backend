from abc import ABC, abstractmethod
from contextlib import asynccontextmanager, contextmanager
from logging import Logger
from typing import Any, NoReturn, Callable
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker, AsyncEngine
from sqlalchemy import create_engine, Engine
from sqlalchemy.exc import ArgumentError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from ...db.types import DatabaseURL, DatabaseSession
from ..exceptions import DatabaseManagerException, DatabaseManagerMessages


class ManagerInterface(ABC):
    """Интерфейс для класса менеджера базы данных."""

    @abstractmethod
    def get_engine(self):
        """Метод получения engine базы данных для прямого использования."""


class ManagerValidator:
    """Класс валидирующий параметры."""

    SUPPORTED_SCHEMES = {"sqlite+aiosqlite", "postgresql+asyncpg", "postgresql", "sqlite", "postgresql+psycopg2"}
    exception = DatabaseManagerException
    messages = DatabaseManagerMessages

    def __init__(self, database_url: DatabaseURL, **kwargs) -> None:
        """Магический метод инициализации класса.

        Args:
            database_url: URL базы данных в формате SQLAlchemy.

        Raises:
            DatabaseManagerException: При любом нарушении формата URL.
        """
        self._database_url = database_url
        self._validate()

    def _validate(self) -> None | NoReturn:
        """Метод запуска процесса валидации.

        Raises:
            DatabaseManagerException: При несоответствии URL требованиям.
        """
        self._validate_database_url(self._database_url)

    def _validate_database_url(self, database_url: Any) -> None:
        """Метод валидации URL базы данных.
        Проверяет:
          - является ли входное значение строкой
          - не пустая ли строка
          - содержит ли схему
          - поддерживается ли схема
          - корректен ли формат для SQLite

        Args:
            database_url: Значение URL базы данных для проверки.

        Raises:
            DatabaseManagerException: При любом нарушении формата.
        """
        if not isinstance(database_url, DatabaseURL):
            raise self.exception(self.messages.INVALID_URL_TYPE_ERROR)

        if not database_url.strip():
            raise self.exception(self.messages.EMPTY_URL_ERROR)

        parsed = urlparse(database_url)
        if not parsed.scheme:
            raise self.exception(self.messages.MISSING_SCHEME_ERROR)

        if parsed.scheme not in self.SUPPORTED_SCHEMES:
            supported = ", ".join(sorted(self.SUPPORTED_SCHEMES))
            message = self.messages.UNSUPPORTED_SCHEME_ERROR.format(scheme=parsed.scheme, supported=supported)
            raise self.exception(message)

        if parsed.scheme == "sqlite+aiosqlite":
            if parsed.netloc and not parsed.path:
                raise self.exception(self.messages.INVALID_SQLITE_FORMAT_ERROR)


class ManagerBase(ManagerValidator):
    """Базовый класс менеджера базы данных."""

    def __init__(self, logger: Logger, database_url: DatabaseURL, **kwargs) -> None:
        """Магический метод инициализации класса.

        Args:
            database_url: URL базы данных в формате SQLAlchemy.

        Raises:
            DatabaseManagerException: При любом нарушении формата URL.
        """
        super().__init__(database_url, **kwargs)

        self._logger = logger
        self._database_url = database_url.strip()

        self._engine = self._create_engine()
        self._sessionmaker = self._create_sessionmaker()

    @property
    @abstractmethod
    def _engine_creator(self):
        """Абстрактное свойство получения функции создания движка."""

    def _create_engine(self) -> Engine | AsyncEngine:
        """Метод создания SQLAlchemy Engine с общей логикой обработки ошибок.

        Returns:
            Инициализированный движок SQLAlchemy.

        Raises:
            DatabaseManagerException: При ошибках создания движка.
        """
        try:
            return self._engine_creator(
                self._database_url,
                pool_pre_ping=True,
                echo=False,
            )
        except ArgumentError as e:
            message = self.messages.INVALID_ENGINE_CONFIG_ERROR.format(error=str(e))
            self._logger.error(message)
            raise self.exception(message) from e
        except Exception as e:
            message = self.messages.ENGINE_CREATION_FAILED_ERROR.format(error=str(e))
            self._logger.error(message)
            raise self.exception(message) from e

    @property
    @abstractmethod
    def _sessionmaker_creator(self) -> Callable[..., sessionmaker | async_sessionmaker]:
        """Абстрактное свойство получения функции создания sessionmaker."""

    def _create_sessionmaker(self) -> sessionmaker | async_sessionmaker:
        """Метод создания sessionmaker с общей логикой обработки ошибок.

        Returns:
            Фабрика сессий SQLAlchemy.

        Raises:
            DatabaseManagerException: При ошибках создания sessionmaker.
        """
        try:
            return self._sessionmaker_creator(
                bind=self._engine,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
            )
        except Exception as e:
            message = self.messages.SESSIONMAKER_CREATION_FAILED_ERROR.format(error=str(e))
            self._logger.error(message)
            raise self.exception(message) from e

    def _handle_session_exception(self, e):
        """Общая логика обработки исключений сессии.

        Args:
            e: Исключение, которое произошло.
        """
        if isinstance(e, SQLAlchemyError):
            message = self.messages.SESSION_ERROR.format(error=str(e))
            self._logger.error(message)
        else:
            message = self.messages.UNEXPECTED_SESSION_ERROR.format(error=str(e))
            self._logger.error(message)
        raise self.exception(message) from e

    def get_engine(self):
        """Метод получения engine базы данных для прямого использования.

        Returns:
            SQLAlchemy Engine, привязанный к указанной базе данных.
        """
        return self._engine


class ManagerAsync(ManagerBase, ManagerInterface):
    """Асинхронный класс менеджера базы данных."""

    def __init__(self, logger: Logger, database_url: DatabaseURL, **kwargs) -> None:
        """Магический метод инициализации класса.

        Args:
            database_url: URL базы данных в формате SQLAlchemy.

        Raises:
            DatabaseManagerException: При любом нарушении формата URL.
        """
        super().__init__(logger, database_url, **kwargs)

    @property
    def _engine_creator(self) -> create_async_engine:
        """Свойство получения функции создания асинхронного движка.

        Returns:
            Функция create_async_engine для создания асинхронного движка.
        """
        return create_async_engine

    @property
    def _sessionmaker_creator(self) -> Callable[..., async_sessionmaker]:
        """Свойство получения функции создания асинхронного sessionmaker.

        Returns:
            Функция async_sessionmaker для создания асинхронного sessionmaker.
        """
        return lambda **kwargs: async_sessionmaker(class_=AsyncSession, **kwargs)

    @asynccontextmanager
    async def get_session(self) -> DatabaseSession:
        """Метод получения генератора сессии базы данных с автоматической очисткой.

        Yields:
            Сессия SQLAlchemy для выполнения запросов.

        Raises:
            Если не удалось создать сессию.
        """
        session: AsyncSession | None = None
        try:
            session = self._sessionmaker()
            yield session
        except Exception as e:
            if session:
                try:
                    await session.rollback()
                except Exception as rollback_err:
                    self._logger.warning(self.messages.ROLLBACK_FAILED_ERROR.format(error=str(rollback_err)))
            self._handle_session_exception(e)
        finally:
            if session:
                try:
                    await session.close()
                except Exception as close_err:
                    self._logger.warning(self.messages.CLOSE_FAILED_ERROR.format(error=str(close_err)))


class ManagerSync(ManagerBase, ManagerInterface):
    """Синхронный класс менеджера базы данных."""

    def __init__(self, logger: Logger, database_url: DatabaseURL, **kwargs) -> None:
        """Магический метод инициализации класса.

        Args:
            database_url: URL базы данных в формате SQLAlchemy.

        Raises:
            DatabaseManagerException: При любом нарушении формата URL.
        """
        super().__init__(logger, database_url, **kwargs)

    @property
    def _engine_creator(self) -> create_engine:
        """Свойство получения функции создания синхронного движка.

        Returns:
            Функция create_engine для создания синхронного движка.
        """
        return create_engine

    @property
    def _sessionmaker_creator(self) -> Callable[..., sessionmaker]:
        """Свойство получения функции создания синхронного sessionmaker.

        Returns:
            Функция sessionmaker для создания синхронного sessionmaker.
        """
        return lambda **kwargs: sessionmaker(class_=Session, **kwargs)

    @contextmanager
    def get_session(self) -> DatabaseSession:
        """Метод получения генератора сессии базы данных с автоматической очисткой.

        Yields:
            Сессия SQLAlchemy для выполнения запросов.

        Raises:
            Если не удалось создать сессию.
        """
        session: Session | None = None
        try:
            session = self._sessionmaker()
            yield session
        except Exception as e:
            if session:
                try:
                    session.rollback()
                except Exception as rollback_err:
                    self._logger.warning(self.messages.ROLLBACK_FAILED_ERROR.format(error=str(rollback_err)))
            self._handle_session_exception(e)
        finally:
            if session:
                try:
                    session.close()
                except Exception as close_err:
                    self._logger.warning(self.messages.CLOSE_FAILED_ERROR.format(error=str(close_err)))
