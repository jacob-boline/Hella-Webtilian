# hr_payment/admin.py

from django.contrib import admin

from hr_payment.models import PaymentAttempt, WebhookEvent, PaymentAttemptStatus


@admin.register(PaymentAttempt)
class PaymentAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "provider",
        "status",
        "amount_cents",
        "currency",
        "provider_session_id",
        "provider_payment_intent_id",
        "created_at",
        "finalized_at",
    )
    list_filter = ("provider", "status", "created_at", "finalized_at")
    search_fields = (
        "order__id",
        "order__customer__email",
        "provider_session_id",
        "provider_payment_intent_id",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "finalized_at",
        "raw",
    )
    ordering = ("-created_at",)

    actions = ["mark_as_succeeded", "mark_as_failed"]

    @admin.action(description="Mark selected attempts as succeeded")
    def mark_as_succeeded(self, request, queryset):
        updated = queryset.update(status=PaymentAttemptStatus.SUCCEEDED)
        self.message_user(request, f"Updated {updated} payment attempt(s) to succeeded.")

    @admin.action(description="Mark selected attempts as failed")
    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status=PaymentAttemptStatus.FAILED)
        self.message_user(request, f"Updated {updated} payment attempt(s) to failed.")


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ("event_id", "type", "ok", "received_at", "processed_at")
    list_filter = ("ok", "type", "received_at", "processed_at")
    search_fields = ("event_id", "type")
    readonly_fields = (
        "payload",
        "received_at",
        "processed_at",
        "event_id",
    )
    ordering = ("-received_at",)
