# hr_shop/views/checkout_stripe.py

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import stripe

from hr_common.security import secrets
from hr_common.utils.unified_logging import log_event

logger = logging.getLogger(__name__)

_InvalidRequestError   = stripe.error.InvalidRequestError
_AuthenticationError   = stripe.error.AuthenticationError
_StripePermissionError = stripe.error.PermissionError
_APIConnectionError    = stripe.error.APIConnectionError
_RateLimitError        = stripe.error.RateLimitError
_StripeError           = stripe.error.StripeError


class StripePaymentResult(str, Enum):
    PAID     = "paid"
    PENDING  = "pending"  # session open / still processing / temporary Stripe issue
    FAILED   = "failed"   # user action required / payment rejected
    CANCELED = "canceled"
    EXPIRED  = "expired"
    UNKNOWN  = "unknown"


class StripeFailureCode(str, Enum):
    MISSING_SESSION_ID      = "missing_session_id"
    INVALID_SESSION         = "invalid_session"
    SESSION_EXPIRED         = "session_expired"
    INVALID_PAYMENT_INTENT  = "invalid_payment_intent"
    PAYMENT_INTENT_CANCELED = "payment_intent_canceled"
    STRIPE_AUTH_ERROR       = "stripe_auth_error"
    STRIPE_ERROR            = "stripe_error"


@dataclass(frozen=True)
class StripePaymentOutcome:
    result: StripePaymentResult
    failure_reason: str | None = None
    failure_code: str | None = None

    def as_tuple(self) -> tuple[str, str | None, str | None]:
        return self.result.value, self.failure_reason, self.failure_code


SESSION_RULES: dict[tuple[str, str], StripePaymentOutcome] = {
    ("complete", "paid"):                StripePaymentOutcome(StripePaymentResult.PAID),
    ("open",     "paid"):                StripePaymentOutcome(StripePaymentResult.PAID),
    ("open",     "unpaid"):              StripePaymentOutcome(StripePaymentResult.PENDING),
    ("open",     "no_payment_required"): StripePaymentOutcome(StripePaymentResult.PAID),
    ("expired",  "paid"):                StripePaymentOutcome(StripePaymentResult.PAID),
    ("expired",  "no_payment_required"): StripePaymentOutcome(StripePaymentResult.EXPIRED),
    ("expired",  "unpaid"):              StripePaymentOutcome(StripePaymentResult.EXPIRED,
                                             "The checkout session expired before payment completed.",
                                             StripeFailureCode.SESSION_EXPIRED)
}


def _stripe_log_temporary(session_id: str, where: str, err: Exception) -> StripePaymentOutcome:
    log_event(logger, logging.INFO, "stripe.session.temporary_issue", where=where, session_id=session_id, error=str(err))
    return StripePaymentOutcome(StripePaymentResult.PENDING)


def _stripe_log_auth_error(session_id: str, where: str, err: Exception) -> StripePaymentOutcome:
    log_event(logger, logging.CRITICAL, "stripe.session.auth_error", where=where, session_id=session_id, error=str(err))
    return StripePaymentOutcome(StripePaymentResult.UNKNOWN, "Payment configuration error.", StripeFailureCode.STRIPE_AUTH_ERROR)


def _stripe_log_generic_error(session_id: str, where: str, err: Exception) -> StripePaymentOutcome:
    log_event(logger, logging.ERROR, "stripe.session.error", where=where, session_id=session_id, error=str(err), exc_info=True)
    return StripePaymentOutcome(StripePaymentResult.UNKNOWN, "Payment processor error.", StripeFailureCode.STRIPE_ERROR)


def _stripe_retrieve_session(session_id: str) -> tuple[Any | None, StripePaymentOutcome | None]:
    """Returns (session, None) on success, (None, outcome) on error."""
    try:
        return stripe.checkout.Session.retrieve(session_id), None
    except _InvalidRequestError as e:
        log_event(logger, logging.WARNING, "stripe.session.invalid", session_id=session_id, error=str(e))
        return None, StripePaymentOutcome(StripePaymentResult.UNKNOWN, "Invalid checkout session.", StripeFailureCode.INVALID_SESSION)
    except (_APIConnectionError, _RateLimitError) as e:
        return None, _stripe_log_temporary(session_id, "retrieve_session", e)
    except (_AuthenticationError, _StripePermissionError) as e:
        return None, _stripe_log_auth_error(session_id, "retrieve_session", e)
    except _StripeError as e:
        return None, _stripe_log_generic_error(session_id, "retrieve_session", e)


def _stripe_retrieve_payment_intent(pi_id: str, session_id: str) -> tuple[Any | None, StripePaymentOutcome | None]:
    """Returns (payment_intent, None) on success, (None, outcome) on error."""
    try:
        return stripe.PaymentIntent.retrieve(pi_id), None
    except _InvalidRequestError as e:
        log_event(logger, logging.WARNING, "stripe.payment_intent.invalid", payment_intent_id=pi_id, session_id=session_id, error=str(e))
        return None, StripePaymentOutcome(StripePaymentResult.UNKNOWN, "Invalid payment intent.", StripeFailureCode.INVALID_PAYMENT_INTENT)
    except (_APIConnectionError, _RateLimitError) as e:
        return None, _stripe_log_temporary(session_id, "retrieve_payment_intent", e)
    except (_AuthenticationError, _StripePermissionError) as e:
        return None, _stripe_log_auth_error(session_id, "retrieve_payment_intent", e)
    except _StripeError as e:
        return None, _stripe_log_generic_error(session_id, "retrieve_payment_intent", e)


def _outcome_from_payment_intent(pi) -> StripePaymentOutcome:
    PI_RULES: dict[str, StripePaymentOutcome] = {
        "succeeded":               StripePaymentOutcome(StripePaymentResult.PAID),
        "canceled":                StripePaymentOutcome(StripePaymentResult.CANCELED, "The payment was canceled.", StripeFailureCode.PAYMENT_INTENT_CANCELED),
        "requires_payment_method": StripePaymentOutcome(StripePaymentResult.FAILED),
        "requires_action":         StripePaymentOutcome(StripePaymentResult.FAILED),
        "requires_confirmation":   StripePaymentOutcome(StripePaymentResult.FAILED),
        "processing":              StripePaymentOutcome(StripePaymentResult.PENDING),
        "requires_capture":        StripePaymentOutcome(StripePaymentResult.PENDING)
    }

    pi_status = (pi.get("status") or "").lower()
    last_err  =  pi.get("last_payment_error") or {}
    reason = last_err.get("message") or None
    code   = last_err.get("code") or None

    mapped = PI_RULES.get(pi_status)
    if not mapped:
        return StripePaymentOutcome(StripePaymentResult.UNKNOWN, reason, code)

    if mapped.result == StripePaymentResult.FAILED:
        return StripePaymentOutcome(StripePaymentResult.FAILED, reason, code or pi_status)

    return mapped


def _stripe_session_payment_intent_id(session_id: str) -> str | None:
    if not session_id:
        return None

    stripe.api_key = secrets.read_secret('STRIPE_SECRET_KEY')

    try:
        sess = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError:
        return None

    return sess.get("payment_intent")


def _stripe_session_result(session_id: str | None) -> tuple[str, str | None, str | None]:
    if not session_id:
        return StripePaymentOutcome(StripePaymentResult.UNKNOWN,
                                    "Missing checkout session id for this order.",
                                    StripeFailureCode.MISSING_SESSION_ID).as_tuple()

    stripe.api_key = secrets.read_secret('STRIPE_SECRET_KEY')

    sess, err = _stripe_retrieve_session(session_id)
    if err:
        return err.as_tuple()

    sess_status = (sess.get("status") or "").lower()
    pay_status  = (sess.get("payment_status") or "").lower()
    pi_id       = sess.get("payment_intent")

    direct = SESSION_RULES.get((sess_status, pay_status))
    if direct:
        return direct.as_tuple()

    if pay_status == "paid":
        return StripePaymentOutcome(StripePaymentResult.PAID).as_tuple()
    if sess_status == "open":
        return StripePaymentOutcome(StripePaymentResult.PENDING).as_tuple()
    if sess_status == "expired":
        return StripePaymentOutcome(StripePaymentResult.EXPIRED,
                                    "The checkout session expired before payment completed.",
                                    StripeFailureCode.SESSION_EXPIRED).as_tuple()

    if not pi_id:
        return StripePaymentOutcome(StripePaymentResult.UNKNOWN).as_tuple()

    pi, err = _stripe_retrieve_payment_intent(pi_id, session_id)
    if err:
        return err.as_tuple()

    return _outcome_from_payment_intent(pi).as_tuple()
