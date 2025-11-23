from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.endpoints import events, healthcheck, analytics
from .api.handlers import (
    method_not_allowed_handler,
    service_unavailable_handler,
    bad_request_error_handler,
    internal_server_error_handler,
    unprocessable_entity_handler,
    events_service_exception_handler,
    usage_service_exception_handler,
    celery_task_timeout_handler,
    celery_broker_unavailable_handler,
)
from app.services.scheduler.exceptions import OrchestratorTimeoutException, OrchestratorBrokerUnavailableException
from .common.logging import setup_logging
from .common.middleware import log_requests_middleware
from .config import CORS_ALLOW_ORIGINS
from .services.events.send_events.exceptions import EventsServiceException
from .services.analytics.usage.exceptions import UsageServiceException

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
app.add_exception_handler(EventsServiceException, events_service_exception_handler)  # Error 422 and 500
app.add_exception_handler(UsageServiceException, usage_service_exception_handler)  # Error 422 and 500

app.add_exception_handler(OrchestratorTimeoutException, celery_task_timeout_handler)  # Error 202
app.add_exception_handler(OrchestratorBrokerUnavailableException, celery_broker_unavailable_handler)  # Error 503

# General exceptions
app.add_exception_handler(RequestValidationError, bad_request_error_handler)  # Error 400
app.add_exception_handler(405, method_not_allowed_handler)
app.add_exception_handler(422, unprocessable_entity_handler)  # Error 422
app.add_exception_handler(500, internal_server_error_handler)
app.add_exception_handler(503, service_unavailable_handler)

app.include_router(healthcheck.router, prefix="/api/v1")
app.include_router(events.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
