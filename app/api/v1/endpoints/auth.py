from fastapi import APIRouter, Body, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from ...dependencies import get_db_session
from ....schemas.auth import (
    # Register
    RegisterRequestSchema,
    RegisterResponseSchema,
    RegisterBadRequestSchema,
    RegisterConflictSchema,
    RegisterUnprocessableEntitySchema,
    RegisterMethodNotAllowedSchema,
    RegisterInternalServerErrorSchema,
    # Login
    LoginRequestSchema,
    LoginResponseSchema,
    LoginBadRequestSchema,
    LoginUnauthorizedSchema,
    LoginForbiddenSchema,
    LoginMethodNotAllowedSchema,
    LoginInternalServerErrorSchema,
    # Refresh
    RefreshRequestSchema,
    RefreshResponseSchema,
    RefreshBadRequestSchema,
    RefreshUnauthorizedSchema,
    RefreshMethodNotAllowedSchema,
    RefreshInternalServerErrorSchema,
    # Verify
    VerifyRequestSchema,
    VerifyResponseSchema,
    VerifyBadRequestSchema,
    VerifyUnauthorizedSchema,
    VerifyUnprocessableEntitySchema,
    VerifyMethodNotAllowedSchema,
    VerifyInternalServerErrorSchema,
    # Resend code
    ResendCodeRequestSchema,
    ResendCodeResponseSchema,
    ResendCodeBadRequestSchema,
    ResendCodeUnauthorizedSchema,
    ResendCodeUnprocessableEntitySchema,
    ResendCodeMethodNotAllowedSchema,
    ResendCodeInternalServerErrorSchema,
)
from ....schemas.general import ServiceUnavailableSchema
from ....services.auth import (
    LoginService,
    RefreshTokensService,
    RegisterService,
    ResendVerificationCodeService,
    VerifyEmailService,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=RegisterResponseSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "model": RegisterResponseSchema,
            "description": "Пользователь создан, код подтверждения отправлен на email",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": RegisterBadRequestSchema,
            "description": "Ошибка первичной валидации запроса",
        },
        status.HTTP_405_METHOD_NOT_ALLOWED: {
            "model": RegisterMethodNotAllowedSchema,
            "description": "Поддерживается только POST метод",
        },
        status.HTTP_409_CONFLICT: {
            "model": RegisterConflictSchema,
            "description": "Email или username уже используется",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": RegisterUnprocessableEntitySchema,
            "description": "Бизнес-валидация входных данных",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": RegisterInternalServerErrorSchema,
            "description": "Внутренняя ошибка сервера",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ServiceUnavailableSchema,
            "description": "Сервис не доступен",
        },
    },
    summary="Регистрация пользователя",
    description="Создаёт пользователя и отправляет код подтверждения на email.",
)
async def register(
    payload: RegisterRequestSchema = Body(..., description="Данные регистрации"),
    db: AsyncSession = Depends(get_db_session),
) -> RegisterResponseSchema:
    user = await RegisterService(
        session=db,
        username=payload.username,
        email=payload.email,
        password=payload.password,
    ).exec()
    return RegisterResponseSchema(
        user_id=str(user.id),
        email=str(user.email),
    )


@router.post(
    "/resend-code",
    response_model=ResendCodeResponseSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": ResendCodeResponseSchema,
            "description": "Код подтверждения отправлен повторно",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ResendCodeBadRequestSchema,
            "description": "Ошибка первичной валидации запроса",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ResendCodeUnauthorizedSchema,
            "description": "Пользователь не найден в системе",
        },
        status.HTTP_405_METHOD_NOT_ALLOWED: {
            "model": ResendCodeMethodNotAllowedSchema,
            "description": "Поддерживается только POST метод",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": ResendCodeUnprocessableEntitySchema,
            "description": "Бизнес-валидация",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ResendCodeInternalServerErrorSchema,
            "description": "Внутренняя ошибка сервера",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ServiceUnavailableSchema,
            "description": "Сервис не доступен",
        },
    },
    summary="Повторная отправка кода подтверждения",
    description="Переиспользует активный код или создаёт новый и отправляет на email.",
)
async def resend_code(
    payload: ResendCodeRequestSchema = Body(..., description="Email для отправки кода"),
    db: AsyncSession = Depends(get_db_session),
) -> ResendCodeResponseSchema:
    await ResendVerificationCodeService(
        session=db,
        email=payload.email,
    ).exec()
    return ResendCodeResponseSchema()


@router.post(
    "/verify",
    response_model=VerifyResponseSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": VerifyResponseSchema,
            "description": "Email успешно подтверждён",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": VerifyBadRequestSchema,
            "description": "Ошибка первичной валидации запроса",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": VerifyUnauthorizedSchema,
            "description": "Пользователь не найден в системе",
        },
        status.HTTP_405_METHOD_NOT_ALLOWED: {
            "model": VerifyMethodNotAllowedSchema,
            "description": "Поддерживается только POST метод",
        },
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "model": VerifyUnprocessableEntitySchema,
            "description": "Бизнес-валидация",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": VerifyInternalServerErrorSchema,
            "description": "Внутренняя ошибка сервера",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ServiceUnavailableSchema,
            "description": "Сервис не доступен",
        },
    },
    summary="Подтверждение email",
    description="Подтверждает email по коду из письма.",
)
async def verify(
    payload: VerifyRequestSchema = Body(..., description="Данные подтверждения email"),
    db: AsyncSession = Depends(get_db_session),
) -> VerifyResponseSchema:
    await VerifyEmailService(
        session=db,
        email=payload.email,
        code=payload.code,
    ).exec()
    return VerifyResponseSchema()


@router.post(
    "/refresh",
    response_model=RefreshResponseSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": RefreshResponseSchema,
            "description": "Токены успешно обновлены",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": RefreshBadRequestSchema,
            "description": "Ошибка первичной валидации запроса",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": RefreshUnauthorizedSchema,
            "description": "Refresh токен невалиден или истёк",
        },
        status.HTTP_405_METHOD_NOT_ALLOWED: {
            "model": RefreshMethodNotAllowedSchema,
            "description": "Поддерживается только POST метод",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": RefreshInternalServerErrorSchema,
            "description": "Внутренняя ошибка сервера",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ServiceUnavailableSchema,
            "description": "Сервис не доступен",
        },
    },
    summary="Обновление токенов",
    description="Принимает refresh токен и возвращает новую пару access/refresh.",
)
async def refresh(
    payload: RefreshRequestSchema = Body(..., description="Данные обновления токена"),
    db: AsyncSession = Depends(get_db_session),
) -> RefreshResponseSchema:
    access_token, refresh_token = await RefreshTokensService(
        session=db,
        refresh_token=payload.refresh_token,
    ).exec()
    return RefreshResponseSchema(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post(
    "/login",
    response_model=LoginResponseSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": LoginResponseSchema,
            "description": "Успешная авторизация",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": LoginBadRequestSchema,
            "description": "Ошибка первичной валидации запроса",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": LoginUnauthorizedSchema,
            "description": "Неверные учётные данные или токен невалиден",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": LoginForbiddenSchema,
            "description": "Email не подтверждён",
        },
        status.HTTP_405_METHOD_NOT_ALLOWED: {
            "model": LoginMethodNotAllowedSchema,
            "description": "Поддерживается только POST метод",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": LoginInternalServerErrorSchema,
            "description": "Внутренняя ошибка сервера",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ServiceUnavailableSchema,
            "description": "Сервис не доступен",
        },
    },
    summary="Авторизация пользователя",
    description="Проверяет учётные данные и возвращает пару access/refresh токенов.",
)
async def login(
    payload: LoginRequestSchema = Body(..., description="Данные авторизации"),
    db: AsyncSession = Depends(get_db_session),
) -> LoginResponseSchema:
    _, access_token, refresh_token = await LoginService(
        session=db,
        username=payload.username,
        password=payload.password,
    ).exec()
    return LoginResponseSchema(
        access_token=access_token,
        refresh_token=refresh_token,
    )
