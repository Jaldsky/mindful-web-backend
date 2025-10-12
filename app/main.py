from fastapi import FastAPI

from .api.v1.endpoints import healthcheck, events
from .common.logging import setup_logging
from .common.middleware import log_requests_middleware

setup_logging()


app = FastAPI(
    title="Mindful-Web service",
    description="Track your web usage and get mindful insights",
    version="0.1.0",
)
app.middleware("http")(log_requests_middleware)

app.include_router(healthcheck.router, prefix="/api/v1")
app.include_router(events.router, prefix="/api/v1")
