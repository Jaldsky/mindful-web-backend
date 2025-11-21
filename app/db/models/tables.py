import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
    CheckConstraint,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from .base import Base


class User(Base):
    """Таблица пользователей системы."""

    __tablename__ = "users"

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Уникальный идентификатор пользователя (UUID4)",
    )
    email = Column(
        String(255),
        unique=True,
        nullable=True,
        index=True,
        comment="Email для авторизации",
    )
    password = Column(String(255), nullable=True, comment="Хэш пароля")
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default="now()", comment="Время регистрации (UTC)"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
        onupdate="now()",
        comment="Время последнего обновления записи (UTC)",
    )
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Время soft-delete",
    )

    attention_events = relationship("AttentionEvent", back_populates="user", cascade="all, delete-orphan")


class DomainCategory(Base):
    """Таблица категорий цифровой активности."""

    __tablename__ = "domain_categories"

    id = Column(Integer, primary_key=True, comment="Автоинкрементный ID категории")
    name = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Уникальное имя категории",
    )
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default="now()", comment="Время создания категории (UTC)"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
        onupdate="now()",
        comment="Время последнего обновления категории",
    )

    domain_to_category = relationship("DomainToCategory", back_populates="category", cascade="all, delete-orphan")


class DomainToCategory(Base):
    """Таблица связи домена с цифровой активностью."""

    __tablename__ = "domain_to_category"

    domain = Column(
        String(255),
        primary_key=True,
        index=True,
        comment="Домен в нижнем регистре (например: 'instagram.com')",
    )
    category_id = Column(
        Integer,
        ForeignKey("domain_categories.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
        comment="Ссылка на категорию из таблицы domain_categories",
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
        comment="Время создания связи (UTC)",
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
        onupdate="now()",
        comment="Время последнего обновления связи (UTC)",
    )

    category = relationship("DomainCategory", back_populates="domain_to_category")


class AttentionEvent(Base):
    """Таблица событий внимания от расширения."""

    __tablename__ = "attention_events"

    id = Column(Integer, primary_key=True, comment="Автоинкрементный ID события")
    user_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True,
        comment="ID пользователя",
    )
    domain = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Домен",
    )
    event_type = Column(
        String(10),
        nullable=False,
        comment="Тип события внимания: active (пользователь перешёл на вкладку) или inactive (покинул вкладку)",
    )
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Точное время события в UTC",
    )

    user = relationship("User", back_populates="attention_events")

    __table_args__ = (
        CheckConstraint(
            text("event_type IN ('active', 'inactive')"),
            name="valid_attention_event_type",
        ),
        Index("idx_attention_events_user_domain_timestamp", "user_id", "domain", "timestamp"),
    )
