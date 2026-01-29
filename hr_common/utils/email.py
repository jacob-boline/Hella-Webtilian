# hr_common/utils/email.py


def normalize_email(value: str) -> str:
    """
    Trim whitespace, lower/normalize case, safely handle None.
    """
    return (value or "").strip().casefold()
