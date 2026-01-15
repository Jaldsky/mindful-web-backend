from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.endpoints import healthcheck, auth, user, events, analytics
from .api.handlers import (
    method_not_allowed_handler,
    service_unavailable_handler,
    bad_request_error_handler,
    internal_server_error_handler,
    unprocessable_entity_handler,
    app_exception_handler,
)
from .exceptions import AppException
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

# Custom exceptions
app.add_exception_handler(AppException, app_exception_handler)

# General exceptions
app.add_exception_handler(RequestValidationError, bad_request_error_handler)  # Error 400
app.add_exception_handler(405, method_not_allowed_handler)
app.add_exception_handler(422, unprocessable_entity_handler)
app.add_exception_handler(500, internal_server_error_handler)
app.add_exception_handler(503, service_unavailable_handler)

app.include_router(healthcheck.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")
app.include_router(events.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
