# hr_shop/exceptions.py

"""
Custom exceptions for the hr_shop app.
"""


class CheckoutError(Exception):
    """Base exception for checkout-related errors."""
    pass


class RateLimitExceeded(CheckoutError):
    """Raised when too many confirmation emails have been sent."""
    pass


class EmailSendError(CheckoutError):
    """Raised when an email fails to send."""
    pass


class SessionExpired(CheckoutError):
    """Raised when checkout session data is missing or expired."""
    pass


class InvalidToken(CheckoutError):
    """Raised when a confirmation token is invalid or expired."""
    pass
