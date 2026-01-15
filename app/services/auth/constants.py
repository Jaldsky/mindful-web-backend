from typing import Literal

# Куки
AUTH_ACCESS_COOKIE_NAME: str = "access_token"
AUTH_REFRESH_COOKIE_NAME: str = "refresh_token"
AUTH_COOKIE_DOMAIN: str = ""
AUTH_COOKIE_PATH: str = "/"
AUTH_COOKIE_SAMESITE: Literal["lax", "strict", "none"] | None = "lax"

# Константы валидации
MIN_USERNAME_LENGTH: int = 3
MAX_USERNAME_LENGTH: int = 50
MIN_PASSWORD_LENGTH: int = 8
MAX_PASSWORD_LENGTH: int = 128
