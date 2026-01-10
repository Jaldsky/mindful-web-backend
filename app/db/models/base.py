from datetime import datetime, timezone
from sqlalchemy import event
from sqlalchemy.orm import declarative_base

Base = declarative_base()


@event.listens_for(Base, "before_update", propagate=True)
def receive_before_update(*_, target):
    """Обработчик события before_update для автоматического обновления поля updated_at.
    Автоматически устанавливает текущее время UTC в поле updated_at при обновлении
    любой записи. Работает для всех моделей, которые наследуются от Base и
    имеют атрибут updated_at.
    Args:
        *_: Игнорируемые позиционные аргументы.
        target: Экземпляр модели, который обновляется.
    """
    if hasattr(target, "updated_at"):
        target.updated_at = datetime.now(timezone.utc)
