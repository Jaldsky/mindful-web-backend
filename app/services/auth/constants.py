from typing import Literal

# Куки
AUTH_ACCESS_COOKIE_NAME: str = "access_token"
AUTH_REFRESH_COOKIE_NAME: str = "refresh_token"
AUTH_ANON_COOKIE_NAME: str = "anon_token"
AUTH_COOKIE_PATH: str = "/"

# Константы валидации
MIN_USERNAME_LENGTH: int = 3
MAX_USERNAME_LENGTH: int = 50
MIN_PASSWORD_LENGTH: int = 8
MAX_PASSWORD_LENGTH: int = 128
