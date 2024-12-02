from django.urls import path
from hr_payment import views

app_name = 'hr_payment'

urlpatterns = [
    path('create-checkout-session/<pk>/', views.CreateCheckoutSessionView.as_view),
    path('webhooks/stripe/', views.stripe_webhook, name='stripe-webhook'),
    path('create-payment-intent/<pk>/', views.StripeIntentView.as_view(), name='create-payment-intent'),
    path('cancel/', views.CancelView.as_view(), name='checkout_cancel'),
    path('success/', views.SuccessView.as_view(), name='checkout_success'),
    path('payment/', views.CustomPaymentView.as_view(), name='custom-payment'),
]
