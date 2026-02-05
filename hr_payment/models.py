# hr_payment/models.py

from __future__ import annotations

from django.db import models
from django.db.models import Q
from django.utils import timezone


class PaymentAttemptStatus(models.TextChoices):
    CREATED = "created"
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELED = "canceled"


class PaymentAttempt(models.Model):
    order = models.ForeignKey("hr_shop.Order", on_delete=models.PROTECT, related_name="payment_attempts")
    provider_session_id = models.CharField(max_length=255, null=True, blank=True)
    client_secret = models.TextField(null=True, blank=True)
    provider_payment_intent_id = models.CharField(max_length=255, null=True, blank=True)
    failure_code = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=20, choices=PaymentAttemptStatus.choices, default=PaymentAttemptStatus.CREATED, db_index=True)
    provider = models.CharField(max_length=32, default="stripe")
    currency = models.CharField(max_length=10, default="usd")
    amount_cents = models.PositiveIntegerField(default=0)
    failure_message = models.TextField(null=True, blank=True)
    raw = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    finalized_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["order", "created_at"]),
            models.Index(fields=["provider_session_id"]),
            models.Index(fields=["provider_payment_intent_id"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["provider_session_id"],
                condition=Q(provider_session_id__isnull=False),
                name="uq_paymentattempt_provider_session_id_not_null",
            ),
            models.UniqueConstraint(
                fields=["provider_payment_intent_id"],
                condition=Q(provider_payment_intent_id__isnull=False),
                name="uq_paymentattempt_payment_intent_id_not_null",
            ),
        ]

    def mark_final(self, new_status: str, *, code: str | None = None, msg: str | None = None):
        self.status = new_status
        self.failure_code = code
        self.failure_message = msg
        self.finalized_at = timezone.now()
        self.save(update_fields=["status", "failure_code", "failure_message", "finalized_at", "updated_at"])


class WebhookEvent(models.Model):
    """
    Idempotency + audit log for inbound webhook payloads.
    """

    event_id = models.CharField(max_length=255, unique=True)
    type = models.CharField(max_length=255, db_index=True)
    payload = models.JSONField()
    received_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)
    ok = models.BooleanField(default=False)
    error = models.TextField(null=True, blank=True)
