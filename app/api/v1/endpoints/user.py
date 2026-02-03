from uuid import UUID

from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from ...dependencies import get_current_user_id, get_db_session
from ...state_services import (
    get_profile_service,
    get_update_email_service,
    get_update_username_service,
)
from ....schemas.user import (
    ProfileResponseSchema,
    ProfileMethodNotAllowedSchema,
    ProfileUnauthorizedSchema,
    ProfileInternalServerErrorSchema,
    UpdateUsernameRequestSchema,
    UpdateUsernameBadRequestSchema,
    UpdateUsernameConflictSchema,
    UpdateUsernameUnprocessableEntitySchema,
    UpdateUsernameMethodNotAllowedSchema,
    UpdateUsernameUnauthorizedSchema,
    UpdateUsernameInternalServerErrorSchema,
    UpdateEmailRequestSchema,
    UpdateEmailBadRequestSchema,
    UpdateEmailConflictSchema,
    UpdateEmailUnprocessableEntitySchema,
    UpdateEmailMethodNotAllowedSchema,
    UpdateEmailUnauthorizedSchema,
    UpdateEmailInternalServerErrorSchema,
)
from ....schemas.general import ServiceUnavailableSchema

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
    profile_service=Depends(get_profile_service),
) -> ProfileResponseSchema:
    """Эндпоинт получения профиля текущего пользователя.

    Args:
        user_id: Идентификатор пользователя из access Bearer JWT.
        db: Сессия базы данных.
        profile_service: Сервис профиля.

    Returns:
        ProfileResponseSchema.

    Raises:
        TokenMissingException: Если заголовок Authorization отсутствует (401).
        TokenInvalidException: Если токен невалиден (401).
        TokenExpiredException: Если токен истёк (401).
        UserNotFoundException: Если пользователь не найден в системе (401).
    """
    profile = await profile_service.exec(session=db, user_id=user_id)
    return ProfileResponseSchema(
        data={
            "username": profile.username,
            "email": profile.email,
        },
    )


@router.patch(
    "/profile/username",
    response_model=ProfileResponseSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": ProfileResponseSchema,
            "description": "Логин пользователя обновлён",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": UpdateUsernameBadRequestSchema,
            "description": "Ошибка первичной валидации запроса",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": UpdateUsernameUnauthorizedSchema,
            "description": "Токен невалиден или пользователь не найден",
        },
        status.HTTP_405_METHOD_NOT_ALLOWED: {
            "model": UpdateUsernameMethodNotAllowedSchema,
            "description": "Поддерживается только PATCH метод",
        },
        status.HTTP_409_CONFLICT: {
            "model": UpdateUsernameConflictSchema,
            "description": "Логин уже используется",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": UpdateUsernameUnprocessableEntitySchema,
            "description": "Бизнес-валидация",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": UpdateUsernameInternalServerErrorSchema,
            "description": "Внутренняя ошибка сервера",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ServiceUnavailableSchema,
            "description": "Сервис не доступен",
        },
    },
    summary="Обновление логина текущего пользователя",
    description="Обновляет username текущего пользователя.",
)
async def update_profile_username(
    payload: UpdateUsernameRequestSchema = Body(..., description="Новый логин пользователя"),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
    update_username_service=Depends(get_update_username_service),
) -> ProfileResponseSchema:
    """Эндпоинт обновления логина текущего пользователя.

    Args:
        payload: Схема с новым логином пользователя.
        user_id: Идентификатор пользователя из access Bearer JWT.
        db: Сессия базы данных.
        update_username_service: Сервис обновления логина.

    Returns:
        ProfileResponseSchema.

    Raises:
        TokenMissingException: Если заголовок Authorization отсутствует (401).
        TokenInvalidException: Если токен невалиден (401).
        TokenExpiredException: Если токен истёк (401).
        UserNotFoundException: Если пользователь не найден в системе (401).
        UsernameAlreadyExistsException: Если логин уже занят (409).
        InvalidUsernameFormatException: Если логин не проходит бизнес-валидацию (422).
    """
    profile = await update_username_service.exec(
        session=db,
        user_id=user_id,
        username=payload.username,
    )
    return ProfileResponseSchema(
        data={
            "username": profile.username,
            "email": profile.email,
        },
    )


@router.patch(
    "/profile/email",
    response_model=ProfileResponseSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": ProfileResponseSchema,
            "description": "Email подтверждается, код подтверждения отправлен",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": UpdateEmailBadRequestSchema,
            "description": "Ошибка первичной валидации запроса",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": UpdateEmailUnauthorizedSchema,
            "description": "Токен невалиден или пользователь не найден",
        },
        status.HTTP_405_METHOD_NOT_ALLOWED: {
            "model": UpdateEmailMethodNotAllowedSchema,
            "description": "Поддерживается только PATCH метод",
        },
        status.HTTP_409_CONFLICT: {
            "model": UpdateEmailConflictSchema,
            "description": "Email уже используется",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": UpdateEmailUnprocessableEntitySchema,
            "description": "Бизнес-валидация",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": UpdateEmailInternalServerErrorSchema,
            "description": "Внутренняя ошибка сервера",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ServiceUnavailableSchema,
            "description": "Сервис не доступен",
        },
    },
    summary="Обновление email текущего пользователя",
    description="Создаёт pending email и отправляет код подтверждения на новый адрес.",
)
async def update_profile_email(
    payload: UpdateEmailRequestSchema = Body(..., description="Новый email пользователя"),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
    update_email_service=Depends(get_update_email_service),
) -> ProfileResponseSchema:
    """Эндпоинт обновления email текущего пользователя.

    Создаёт pending_email и отправляет код подтверждения на новый адрес.

    Args:
        payload: Схема с новым email пользователя.
        user_id: Идентификатор пользователя из access Bearer JWT.
        db: Сессия базы данных.
        update_email_service: Сервис обновления email.

    Returns:
        ProfileResponseSchema.

    Raises:
        TokenMissingException: Если заголовок Authorization отсутствует (401).
        TokenInvalidException: Если токен невалиден (401).
        TokenExpiredException: Если токен истёк (401).
        UserNotFoundException: Если пользователь не найден в системе (401).
        EmailAlreadyExistsException: Если email уже занят (409).
        InvalidEmailFormatException: Если email не проходит бизнес-валидацию (422).
        EmailSendFailedException: Если отправка кода подтверждения не удалась (500).
    """
    profile = await update_email_service.exec(
        session=db,
        user_id=user_id,
        email=payload.email,
    )
    return ProfileResponseSchema(
        data={
            "username": profile.username,
            "email": profile.email,
        },
    )
