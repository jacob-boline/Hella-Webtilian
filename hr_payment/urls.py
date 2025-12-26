# hr_payment/urls.py

from django.urls import path
from hr_payment import views

app_name = "hr_payment"

urlpatterns = [
    path("webhooks/stripe/", views.stripe_webhook, name="stripe-webhook"),
    path("checkout/stripe/session/<int:order_id>/", views.checkout_stripe_session, name="checkout_stripe_session"),
]
