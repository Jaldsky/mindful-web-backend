import os

POSTGRES_USER: str = os.getenv("POSTGRES_USER", "root")
POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "root")
POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "mwb-db")
POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", 5432)
POSTGRES_DB: str = os.getenv("POSTGRES_DB", "mindfulweb")

DATABASE_ASYNC_URL: str = os.getenv(
    "DATABASE_ASYNC_URL",
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
)
DATABASE_SYNC_URL: str = os.getenv(
    "DATABASE_SYNC_URL",
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
)

REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "root")
REDIS_HOST: str = os.getenv("REDIS_HOST", "mwb-redis")
REDIS_PORT: str = os.getenv("REDIS_PORT", 6379)
REDIS_DB: str = os.getenv("REDIS_DB", 0)

REDIS_URL: str = os.getenv("REDIS_URL", f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")

CORS_ALLOW_ORIGINS: list[str] = os.getenv("CORS_ALLOW_ORIGINS", "chrome-extension://*").split(",")
