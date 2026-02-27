# hr_shop/urls.py

from django.urls import path

from hr_shop.views import cart, checkout, manage_unified, products

app_name = "hr_shop"

urlpatterns = [
    # Products (front-end)
    path("<slug:product_slug>/modal/", products.get_product_modal_partial, name="get_product_modal_partial"),
    path("merchModule/<slug:product_slug>/modal/", products.get_product_modal_partial, name="product_modal_partial"),
    path("product/<slug:product_slug>/variant-preview", products.update_details_modal, name="update_details_modal"),
    path("product/<slug:product_slug>/image-for-selection/", products.product_image_for_selection, name="product_image_for_selection"),
    # Admin: main product manager shell
    path("manage/", manage_unified.product_manager, name="product_manager"),
    # Cart
    path("cart/add/<slug:variant_slug>/", cart.add_variant_to_cart, name="add_to_cart"),
    path("cart/add/by-options/<slug:product_slug>/", cart.add_to_cart_by_options, name="add_to_cart_by_options"),
    path("cart/update/<int:variant_id>/", cart.set_cart_quantity, name="set_cart_quantity"),
    path("cart/remove/<int:variant_id>/", cart.remove_from_cart, name="remove_from_cart"),
    path("cart/", cart.view_cart, name="view_cart"),
    # Checkout flow
    path("checkout/details/", checkout.checkout_details, name="checkout_details"),
    path("checkout/details/submit", checkout.checkout_details_submit, name="checkout_details_submit"),
    path("checkout/review/", checkout.checkout_review, name="checkout_review"),
    path("checkout/create/", checkout.checkout_create_order, name="checkout_create_order"),
    path("checkout/resume/", checkout.checkout_resume, name="checkout_resume"),
    # path('order/<int:order_id>/payment-result/', checkout.order_payment_result, name='order_payment_result'),
    path("order/payment-result/", checkout.order_payment_result, name="order_payment_result"),
    path("order/<int:order_id>/receipt/send/", checkout.order_send_receipt_email, name="order_send_receipt_email"),
    path("order/<int:order_id>/post-purchase-cta/acknowledged/", checkout.dismiss_post_purchase_cta, name="dismiss_post_purchase_cta"),
    path("checkout/pay/<int:order_id>/", checkout.checkout_pay, name="checkout_pay"),
    # Email confirmation
    path("checkout/confirm/<str:token>/", checkout.email_confirmation_process_response, name="email_confirmation_process_response"),
    path("checkout/check-confirmed/", checkout.email_confirmation_status, name="email_confirmation_status"),
    path("checkout/resend_confirmation/", checkout.email_confirmation_resend, name="email_confirmation_resend"),
    path("checkout/email_confirmation_success/", checkout.email_confirmation_success, name="email_confirmation_success"),
]
