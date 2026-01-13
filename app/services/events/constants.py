ALLOWED_EVENT_TYPES: set[str] = {"active", "inactive"}
MAX_EVENTS_PER_REQUEST: int = 100
MAX_DOMAIN_LENGTH: int = 255

DOMAIN_ALLOWED_RE: str = r"^[a-z0-9.-]+$"
