from email_validator import validate_email

from .types import Email


def validate_email_format(email: Email) -> None:
    """Валидация формата email адреса.

    Args:
        email: Email адрес для валидации.
    """
    validate_email(email, check_deliverability=False)
