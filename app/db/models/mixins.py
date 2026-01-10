from datetime import datetime
from sqlalchemy.orm import Mapped

from sqlalchemy import DateTime, Column


class CreatedMixin:
    """Миксин для добавления поля времени создания записи created_at."""

    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
        comment="Время создания записи (UTC)",
    )


class UpdatedMixin:
    """Миксин для добавления поля обновления записи updated_at."""

    updated_at: Mapped[datetime] = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
        comment="Время последнего обновления записи (UTC)",
    )


class DeletedMixin:
    """Миксин для добавления поля удаления записи deleted_at (soft delete)."""

    deleted_at: Mapped[datetime | None] = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Время удаления записи (UTC)",
    )
