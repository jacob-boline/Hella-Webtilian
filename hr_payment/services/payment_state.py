# hr_payment/services/payment_state.py
import logging

from django.utils import timezone

from hr_common.utils.unified_logging import log_event
from hr_shop.models import CheckoutDraft

logger = logging.getLogger(__name__)

def mark_checkout_draft_used(order_id: int) -> None:
    qs = CheckoutDraft.objects.filter(order_id=order_id)
    updated = qs.filter(used_at__isnull=True).update(used_at=timezone.now())

    if updated == 0:
        if not qs.exists():
            log_event(logger, logging.WARNING, "checkout.draft.invalidate.missing", order_id=order_id)
        else:
            log_event(logger, logging.WARNING, "checkout.draft.invalidate.already_consumed", order_id=order_id)
