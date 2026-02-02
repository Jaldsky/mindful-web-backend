from contextlib import asynccontextmanager
from fastapi import FastAPI

from .localizer import Localizer


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Асинхронная функция контекстного менеджера жизненного цикла приложения.

    Args:
        app: Экземпляр FastAPI-приложения.
    """
    app.state.localizer = Localizer()  # type: ignore[attr-defined]
    yield
