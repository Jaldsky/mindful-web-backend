from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from ...dependencies import get_current_user_id, get_db_session
from ....schemas.user import (
    ProfileResponseSchema,
    ProfileMethodNotAllowedSchema,
    ProfileUnauthorizedSchema,
    ProfileInternalServerErrorSchema,
)
from ....schemas.general import ServiceUnavailableSchema
from ....services.user import ProfileService

router = APIRouter(prefix="/user", tags=["user"])


@router.get(
    "/profile",
    response_model=ProfileResponseSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": ProfileResponseSchema,
            "description": "Профиль пользователя",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ProfileUnauthorizedSchema,
            "description": "Токен невалиден или пользователь не найден",
        },
        status.HTTP_405_METHOD_NOT_ALLOWED: {
            "model": ProfileMethodNotAllowedSchema,
            "description": "Поддерживается только GET метод",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ProfileInternalServerErrorSchema,
            "description": "Внутренняя ошибка сервера",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ServiceUnavailableSchema,
            "description": "Сервис не доступен",
        },
    },
    summary="Профиль текущего пользователя",
    description="Возвращает данные текущего пользователя.",
)
async def get_profile(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
) -> ProfileResponseSchema:
    """Эндпоинт получения профиля текущего пользователя.

    Args:
        user_id: Идентификатор пользователя из access Bearer JWT.
        db: Сессия базы данных.

    Returns:
        UserProfileResponseSchema: Данные профиля пользователя.

    Raises:
        TokenMissingException: Если заголовок Authorization отсутствует (401).
        TokenInvalidException: Если токен невалиден (401).
        TokenExpiredException: Если токен истёк (401).
        UserNotFoundException: Если пользователь не найден в системе (401).
    """
    profile = await ProfileService(session=db, user_id=user_id).exec()
    return ProfileResponseSchema(
        data={
            "username": profile.username,
            "email": profile.email,
        },
    )
