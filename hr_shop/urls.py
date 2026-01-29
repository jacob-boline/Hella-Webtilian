# hr_shop/urls.py

from django.urls import path

from hr_shop.views import cart, checkout, manage, products

app_name = "hr_shop"

urlpatterns = [
    # Products (front-end)
    path("<slug:product_slug>/modal/", products.get_product_modal_partial, name="get_product_modal_partial"),
    path("merchModule/<slug:product_slug>/modal/", products.get_product_modal_partial, name="product_modal_partial"),
    path("product/<slug:product_slug>/variant-preview", products.update_details_modal, name="update_details_modal"),
    path("product/<slug:product_slug>/image-for-selection/", products.product_image_for_selection, name="product_image_for_selection"),
    # Admin: main product manager shell
    path("manage/", manage.product_manager, name="product_manager"),
    # Admin: product management partials
    path("manage/products/", manage.get_manage_product_list_partial, name="get_product_list_partial"),
    path("manage/product/<int:pk>/", manage.get_manage_product_panel_partial, name="get_product_panel_partial"),
    path("manage/option-type/<int:pk>/", manage.get_manage_option_type_panel_partial, name="get_manage_option_type_panel_partial"),
    path("manage/product/<int:pk>/update/", manage.update_product, name="update_product"),
    # Admin: OptionType CRUD
    path("manage/product/<int:product_pk>/option-type/create/", manage.create_option_type, name="create_option_type"),
    path("manage/option-type/<int:pk>/update/", manage.update_option_type, name="update_option_type"),
    path("manage/option-type/<int:pk>/delete/", manage.delete_option_type, name="delete_option_type"),
    # Admin: OptionValue CRUD
    path("manage/option-type/<int:option_type_pk>/value/create/", manage.create_option_value, name="create_option_value"),
    path("manage/option-value/<int:pk>/update/", manage.update_option_value, name="update_option_value"),
    path("manage/option-value/<int:pk>/delete/", manage.delete_option_value, name="delete_option_value"),
    # Admin: Product CRUD
    path("manage/product/<int:product_pk>/variant/create/", manage.create_variant, name="create_variant"),
    path("manage/product/create/", manage.create_product, name="create_product"),
    # Admin: Variant CRUD
    path("manage/variant/<int:pk>/update/", manage.update_variant, name="update_variant"),
    path("manage/variant/<int:pk>/delete/", manage.delete_variant, name="delete_variant"),
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
