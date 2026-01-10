from .types import Email


def normalize_email(email: Email) -> Email:
    """Нормализация email адреса.

    Args:
        email: Email адрес для нормализации.

    Returns:
        Нормализованный email.
    """
    return (email or "").strip().lower()
