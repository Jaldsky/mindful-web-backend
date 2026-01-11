"""Константы путей API endpoints."""

API_V1_PREFIX = "/api/v1"

HEALTHCHECK_PATH = f"{API_V1_PREFIX}/healthcheck"
EVENTS_PATH = f"{API_V1_PREFIX}/events"

SEND_EVENTS_PATH = f"{EVENTS_PATH}/send"
ANALYTICS_USAGE_PATH = f"{API_V1_PREFIX}/analytics/usage"

# Auth
AUTH_PATH = f"{API_V1_PREFIX}/auth"
AUTH_REGISTER_PATH = f"{AUTH_PATH}/register"
AUTH_LOGIN_PATH = f"{AUTH_PATH}/login"
AUTH_REFRESH_PATH = f"{AUTH_PATH}/refresh"
AUTH_VERIFY_PATH = f"{AUTH_PATH}/verify"
AUTH_RESEND_CODE_PATH = f"{AUTH_PATH}/resend-code"
