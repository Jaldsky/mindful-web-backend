from ...core.common import StringEnum


class EmailErrorCode(StringEnum):
    """Коды ошибок сервиса электронной почты."""

    # 422
    INVALID_VERIFICATION_CODE = "INVALID_VERIFICATION_CODE"
    INVALID_EMAIL = "INVALID_EMAIL"
    # 500
    EMAIL_SEND_FAILED = "EMAIL_SEND_FAILED"
    INVALID_SMTP_CONFIG = "INVALID_SMTP_CONFIG"
