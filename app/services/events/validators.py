import re
from datetime import timezone
from typing import NoReturn
from uuid import UUID

from ...schemas import ErrorDetailData
from .constants import ALLOWED_EVENT_TYPES, DOMAIN_ALLOWED_RE, MAX_DOMAIN_LENGTH, MAX_EVENTS_PER_REQUEST
from .exceptions import (
    EmptyEventsListException,
    InvalidDomainFormatException,
    InvalidDomainLengthException,
    InvalidEventTypeException,
    InvalidUserIdException,
    TimestampInFutureException,
    TooManyEventsException,
)
from .types import Domain, EventTimestamp, EventType, UserIdHeader


class EventsServiceValidators:
    """Валидаторы для events-сервиса."""

    _DOMAIN_ALLOWED_RE = re.compile(DOMAIN_ALLOWED_RE)

    @classmethod
    def validate_event_type(cls, event_type: EventType) -> None | NoReturn:
        """Метод валидации типа события.

        Args:
            event_type: Тип события для валидации.

        Raises:
            InvalidEventTypeException: Если event_type не соответствует требованиям.
        """
        if event_type not in ALLOWED_EVENT_TYPES:
            raise InvalidEventTypeException(
                key="events.errors.invalid_event_type",
                fallback="Event must be either active or inactive",
            )

    @classmethod
    def validate_domain(cls, domain: Domain) -> None | NoReturn:
        """Метод валидации домена.

        Args:
            domain: Домен для валидации.

        Raises:
            InvalidDomainFormatException: Если домен имеет неверный формат.
            InvalidDomainLengthException: Если домен слишком длинный.
        """
        if not domain or not isinstance(domain, str):
            raise InvalidDomainFormatException(
                key="events.errors.domain_must_be_non_empty_string",
                fallback="Domain must be a non-empty string",
            )

        if "." not in domain:
            raise InvalidDomainFormatException(
                key="events.errors.domain_must_contain_dot",
                fallback="Invalid domain format: must contain at least one dot",
            )

        if len(domain) > MAX_DOMAIN_LENGTH:
            raise InvalidDomainLengthException(
                key="events.errors.invalid_domain_length",
                fallback="Domain is invalid or too long after normalization",
            )

        if not cls._DOMAIN_ALLOWED_RE.match(domain):
            raise InvalidDomainFormatException(
                key="events.errors.domain_invalid_chars",
                fallback="Domain contains invalid characters",
            )

        if domain.startswith(".") or domain.endswith(".") or domain.startswith("-") or domain.endswith("-"):
            raise InvalidDomainFormatException(
                key="events.errors.domain_cannot_start_or_end",
                fallback="Domain cannot start or end with dot or dash",
            )

    @classmethod
    def validate_timestamp_not_in_future(cls, ts: EventTimestamp) -> None | NoReturn:
        """Метод валидации временной метки.

        Args:
            ts: Временная метка для валидации.

        Raises:
            TimestampInFutureException: Если временная метка в будущем.
        """
        from datetime import datetime

        now = datetime.now(timezone.utc)
        if ts > now:
            raise TimestampInFutureException(
                key="events.errors.timestamp_in_future",
                fallback="Timestamp cannot be in the future",
            )

    @classmethod
    def validate_events_list(cls, data: list) -> None | NoReturn:
        """Метод валидации списка событий.

        Args:
            data: Список событий для валидации.

        Raises:
            EmptyEventsListException: Если список событий пустой.
            TooManyEventsException: Если количество событий превышает лимит.
        """
        if not data or len(data) == 0:
            raise EmptyEventsListException(
                key="events.errors.empty_events_list",
                fallback="Events list cannot be empty",
            )
        if len(data) > MAX_EVENTS_PER_REQUEST:
            raise TooManyEventsException(
                key="events.errors.too_many_events",
                fallback="Events list cannot contain more than 100 events",
            )

    @classmethod
    def validate_user_id_header(cls, x_user_id: UserIdHeader) -> UserIdHeader | NoReturn:
        """Метод валидации заголовка X-User-ID.

        Args:
            x_user_id: Значение заголовка X-User-ID для валидации.

        Returns:
            Валидный UUID4 строкой.

        Raises:
            InvalidUserIdException: Если x_user_id не является валидным UUID4.
        """
        key = "events.errors.invalid_user_id"
        details = [
            ErrorDetailData(
                field="X-User-ID",
                message=key,
                value=x_user_id,
            )
        ]

        try:
            user_uuid = UUID(x_user_id)
            if user_uuid.version != 4:
                raise InvalidUserIdException(
                    key=key,
                    fallback="X-User-ID must be a valid UUID4 string",
                    details=details,
                )
            return x_user_id
        except (ValueError, AttributeError, TypeError):
            raise InvalidUserIdException(
                key=key,
                fallback="X-User-ID must be a valid UUID4 string",
                details=details,
            )
