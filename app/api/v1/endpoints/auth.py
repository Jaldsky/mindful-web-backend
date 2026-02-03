from uuid import UUID

from fastapi import APIRouter, Body, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from ...dependencies import (
    get_db_session,
    get_anonymous_service,
    get_register_service,
    get_login_service,
    get_refresh_tokens_service,
    get_resend_verification_code_service,
    get_verify_email_service,
    get_session_service,
)
from ....schemas.auth import (
    # Anonymous
    AnonymousResponseSchema,
    AnonymousMethodNotAllowedSchema,
    AnonymousInternalServerErrorSchema,
    # Session
    SessionResponseSchema,
    SessionMethodNotAllowedSchema,
    SessionInternalServerErrorSchema,
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
    # Logout
    LogoutResponseSchema,
    LogoutMethodNotAllowedSchema,
    LogoutInternalServerErrorSchema,
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
from ....services.auth.cookies import (
    set_auth_cookies,
    clear_auth_cookies,
    set_anon_cookie,
    clear_anon_cookie,
)
from ....services.auth.exceptions import TokenMissingException
from ....services.auth.constants import AUTH_ACCESS_COOKIE_NAME, AUTH_REFRESH_COOKIE_NAME, AUTH_ANON_COOKIE_NAME
from ....services.auth.common import decode_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/anonymous",
    response_model=AnonymousResponseSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "model": AnonymousResponseSchema,
            "description": "Анонимная сессия создана",
        },
        status.HTTP_405_METHOD_NOT_ALLOWED: {
            "model": AnonymousMethodNotAllowedSchema,
            "description": "Поддерживается только POST метод",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": AnonymousInternalServerErrorSchema,
            "description": "Внутренняя ошибка сервера",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ServiceUnavailableSchema,
            "description": "Сервис не доступен",
        },
    },
    summary="Создание анонимной сессии",
    description="Возвращает идентификатор анонимного пользователя.",
)
async def create_anonymous(
    request: Request,
    response: Response,
    anonymous_service=Depends(get_anonymous_service),
) -> AnonymousResponseSchema:
    """Создаёт анонимную сессию или возвращает существующую по cookie.

    Args:
        request: HTTP-запрос.
        response: HTTP-ответ.
        anonymous_service: Сервис создания анонимной сессии.

    Returns:
        AnonymousResponseSchema.
    """
    anon_token = request.cookies.get(AUTH_ANON_COOKIE_NAME)
    if anon_token:
        try:
            payload = decode_token(anon_token)
            if payload.get("type") == "anon":
                anon_id = UUID(str(payload.get("sub")))
                set_anon_cookie(response, anon_token)
                return AnonymousResponseSchema(
                    anon_id=str(anon_id),
                )
        except Exception:
            "Если cookie истекла или невалидна, то создаем новую"

    anon_id, anon_token = await anonymous_service.exec()
    set_anon_cookie(response, anon_token)
    return AnonymousResponseSchema(anon_id=str(anon_id))


@router.get(
    "/session",
    response_model=SessionResponseSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": SessionResponseSchema,
            "description": "Статус текущей сессии",
        },
        status.HTTP_405_METHOD_NOT_ALLOWED: {
            "model": SessionMethodNotAllowedSchema,
            "description": "Поддерживается только GET метод",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": SessionInternalServerErrorSchema,
            "description": "Внутренняя ошибка сервера",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ServiceUnavailableSchema,
            "description": "Сервис не доступен",
        },
    },
    summary="Проверка текущей сессии",
    description="Проверяет наличие активной сессии в cookies. Не создаёт новую сессию.",
)
async def get_session(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    session_service=Depends(get_session_service),
) -> SessionResponseSchema:
    """Проверяет наличие активной сессии по cookies (access или anon).

    Args:
        request: HTTP-запрос.
        db: Сессия БД.
        session_service: Сервис проверки сессии.

    Returns:
        SessionResponseSchema.
    """
    access_token = request.cookies.get(AUTH_ACCESS_COOKIE_NAME)
    anon_token = request.cookies.get(AUTH_ANON_COOKIE_NAME)

    session_state = await session_service.exec(
        session=db,
        access_token=access_token,
        anon_token=anon_token,
    )

    return SessionResponseSchema(
        status=session_state.status,
        user_id=str(session_state.user_id) if session_state.user_id else None,
        anon_id=str(session_state.anon_id) if session_state.anon_id else None,
    )


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
    register_service=Depends(get_register_service),
) -> RegisterResponseSchema:
    """Регистрирует пользователя и отправляет код подтверждения на email.

    Args:
        payload: username, email, password.
        db: Сессия БД.
        register_service: Сервис регистрации.

    Returns:
        RegisterResponseSchema.

    Raises:
        UsernameAlreadyExistsException: Логин уже занят (409).
        EmailAlreadyExistsException: Email уже занят (409).
        InvalidUsernameFormatException, InvalidEmailFormatException, InvalidPasswordFormatException: Бизнес-валидация (422).
        EmailSendFailedException: Ошибка отправки письма (500).
    """
    user = await register_service.exec(
        session=db,
        username=payload.username,
        email=payload.email,
        password=payload.password,
    )
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
    resend_verification_code_service=Depends(get_resend_verification_code_service),
) -> ResendCodeResponseSchema:
    """Повторно отправляет код подтверждения на email.

    Args:
        payload: email.
        db: Сессия БД.
        resend_verification_code_service: Сервис повторной отправки кода.

    Returns:
        ResendCodeResponseSchema.

    Raises:
        UserNotFoundException: Пользователь не найден (401).
        EmailAlreadyVerifiedException: Email уже подтверждён (422).
        TooManyAttemptsException: Cooldown не прошёл (422).
        EmailSendFailedException: Ошибка отправки письма (500).
    """
    await resend_verification_code_service.exec(session=db, email=payload.email)
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
    verify_email_service=Depends(get_verify_email_service),
) -> VerifyResponseSchema:
    """Подтверждает email по коду из письма.

    Args:
        payload: email и code.
        db: Сессия БД.
        verify_email_service: Сервис подтверждения email.

    Returns:
        VerifyResponseSchema.

    Raises:
        UserNotFoundException: Пользователь не найден (401).
        InvalidVerificationCodeException: Код неверен или истёк (422).
    """
    await verify_email_service.exec(
        session=db,
        email=payload.email,
        code=payload.code,
    )
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
    request: Request,
    response: Response,
    payload: RefreshRequestSchema | None = Body(None, description="Данные обновления токена"),
    db: AsyncSession = Depends(get_db_session),
    refresh_tokens_service=Depends(get_refresh_tokens_service),
) -> RefreshResponseSchema:
    """Обновляет пару access и refresh токенов по refresh-токену (из тела или cookie).

    Args:
        request: HTTP-запрос.
        response: HTTP-ответ.
        payload: Опционально refresh_token в теле.
        db: Сессия БД.
        refresh_tokens_service: Сервис обновления токенов.

    Returns:
        RefreshResponseSchema.

    Raises:
        TokenMissingException: Refresh-токен не передан (401).
        TokenInvalidException, TokenExpiredException: Токен невалиден или истёк (401).
    """
    refresh_token = payload.refresh_token if payload else None
    if not refresh_token:
        refresh_token = request.cookies.get(AUTH_REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise TokenMissingException("auth.errors.token_missing")

    access_token, refresh_token = await refresh_tokens_service.exec(
        session=db,
        refresh_token=refresh_token,
    )

    set_auth_cookies(response, access_token, refresh_token)

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
    response: Response,
    payload: LoginRequestSchema = Body(..., description="Данные авторизации"),
    db: AsyncSession = Depends(get_db_session),
    login_service=Depends(get_login_service),
) -> LoginResponseSchema:
    """Авторизует пользователя по username и password.

    Args:
        response: HTTP-ответ.
        payload: username и password.
        db: Сессия БД.
        login_service: Сервис авторизации.

    Returns:
        LoginResponseSchema.

    Raises:
        InvalidCredentialsException: Неверные учётные данные (401).
        EmailNotVerifiedException: Email не подтверждён (403).
    """
    _, access_token, refresh_token = await login_service.exec(
        session=db,
        username=payload.username,
        password=payload.password,
    )

    clear_anon_cookie(response)
    set_auth_cookies(response, access_token, refresh_token)

    return LoginResponseSchema(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post(
    "/logout",
    response_model=LogoutResponseSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": LogoutResponseSchema,
            "description": "Авторизация пользователя отозвана",
        },
        status.HTTP_405_METHOD_NOT_ALLOWED: {
            "model": LogoutMethodNotAllowedSchema,
            "description": "Поддерживается только POST метод",
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": LogoutInternalServerErrorSchema,
            "description": "Внутренняя ошибка сервера",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ServiceUnavailableSchema,
            "description": "Сервис не доступен",
        },
    },
    summary="Выход пользователя из системы",
    description="Удаляет токен доступа и токен обновления из HTTP куки.",
)
async def logout(response: Response) -> LogoutResponseSchema:
    """Выход из системы: удаляет access, refresh и anon cookies.

    Args:
        response: HTTP-ответ.

    Returns:
        LogoutResponseSchema.
    """
    clear_auth_cookies(response)
    clear_anon_cookie(response)
    return LogoutResponseSchema()
