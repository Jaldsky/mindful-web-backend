from datetime import datetime

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..types import Email, UserId, VerificationCode
from .types import Username
from ...db.models.tables import User, VerificationCode as VerificationCodeModel


async def fetch_users_by_username_or_email(session: AsyncSession, username: Username, email: Email) -> list[User]:
    """Функция получения пользователей по username или email.

    Args:
        session: AsyncSession.
        username: Username пользователя.
        email: Email пользователя.

    Returns:
        Пустой список или список найденных пользователей.
    """
    result = await session.execute(
        select(User).where(
            and_(
                User.deleted_at.is_(None),
                or_(User.username == username, User.email == email),
            )
        )
    )
    return list(result.scalars().all())


async def fetch_user_by_email(session: AsyncSession, email: Email) -> User | None:
    """Функция получения пользователя по email.

    Args:
        session: AsyncSession.
        email: Email пользователя.

    Returns:
        Пользователь или None, если не найден.
    """
    result = await session.execute(select(User).where(and_(User.email == email, User.deleted_at.is_(None))))
    return result.scalar_one_or_none()


async def fetch_active_verification_code_row(
    session: AsyncSession, user_id: UserId, now: datetime
) -> VerificationCodeModel | None:
    """Функция получения активного кода подтверждения пользователя.

    Args:
        session: AsyncSession.
        user_id: ID пользователя.
        now: Текущее время (UTC).

    Returns:
        Активная запись кода или None.
    """
    result = await session.execute(
        select(VerificationCodeModel)
        .where(
            and_(
                VerificationCodeModel.user_id == user_id,
                VerificationCodeModel.used_at.is_(None),
                VerificationCodeModel.expires_at > now,
            )
        )
        .order_by(VerificationCodeModel.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def fetch_unused_verification_code_row_by_user_and_code(
    session: AsyncSession, user_id: UserId, code: VerificationCode
) -> VerificationCodeModel | None:
    """Функция получения кода подтверждения по user_id и code.

    Args:
        session: AsyncSession.
        user_id: ID пользователя.
        code: Код подтверждения.

    Returns:
        Запись кода или None, если не найдена.
    """
    result = await session.execute(
        select(VerificationCodeModel)
        .where(
            and_(
                VerificationCodeModel.user_id == user_id,
                VerificationCodeModel.code == code,
                VerificationCodeModel.used_at.is_(None),
            )
        )
        .order_by(VerificationCodeModel.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def update_verification_code_last_sent_at(
    session: AsyncSession, verification_code_id: int, at: datetime
) -> None:
    """Функция обновления времени последней отправки кода (last_sent_at).

    Args:
        session: AsyncSession.
        verification_code_id: ID записи кода в таблице verification_codes.
        at: Время обновления (UTC).
    """
    await session.execute(
        update(VerificationCodeModel).where(VerificationCodeModel.id == verification_code_id).values(last_sent_at=at)
    )
