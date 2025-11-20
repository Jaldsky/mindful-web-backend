from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.endpoints import events, healthcheck
from .api.handlers import method_not_allowed_handler, service_unavailable_handler
from .common.logging import setup_logging
from .common.middleware import log_requests_middleware
from .config import CORS_ALLOW_ORIGINS

setup_logging()


app = FastAPI(
    title="Mindful-Web service",
    description="Track your web usage and get mindful insights",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.middleware("http")(log_requests_middleware)

# General exceptions
app.add_exception_handler(405, method_not_allowed_handler)
app.add_exception_handler(503, service_unavailable_handler)

app.include_router(healthcheck.router, prefix="/api/v1")
app.include_router(events.router, prefix="/api/v1")
