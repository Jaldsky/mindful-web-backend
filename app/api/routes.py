"""Константы путей API endpoints."""

API_V1_PREFIX = "/api/v1"

# Healthcheck
HEALTHCHECK_PATH = f"{API_V1_PREFIX}/healthcheck"

# Auth
AUTH_PATH = f"{API_V1_PREFIX}/auth"
AUTH_REGISTER_PATH = f"{AUTH_PATH}/register"
AUTH_LOGIN_PATH = f"{AUTH_PATH}/login"
AUTH_REFRESH_PATH = f"{AUTH_PATH}/refresh"
AUTH_VERIFY_PATH = f"{AUTH_PATH}/verify"
AUTH_RESEND_CODE_PATH = f"{AUTH_PATH}/resend-code"

# User
USER_PATH = f"{API_V1_PREFIX}/user"
USER_PROFILE_PATH = f"{USER_PATH}/profile"

# Events
EVENTS_PATH = f"{API_V1_PREFIX}/events"
SEND_EVENTS_PATH = f"{EVENTS_PATH}/save"

# Analytics
ANALYTICS_USAGE_PATH = f"{API_V1_PREFIX}/analytics/usage"
