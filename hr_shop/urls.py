# hr_shop/urls.py

from django.urls import path
from hr_shop.views import products, cart, manage, checkout

app_name = 'hr_shop'

urlpatterns = [

    # Products (front-end)

    path('<slug:product_slug>/modal/', products.get_product_modal_partial, name='get_product_modal_partial'),
    path('merchModule/<slug:product_slug>/modal/', products.get_product_modal_partial, name='product_modal_partial'),
    path('product/<slug:product_slug>/variant-preview', products.update_details_modal, name='update_details_modal'),
    path('product/<slug:product_slug>/image-for-selection/', products.product_image_for_selection, name='product_image_for_selection'),

    # Admin: main product manager shell

    path('manage/', manage.product_manager, name='product_manager'),


    # Admin: product management partials

    path('manage/products/', manage.get_manage_product_list_partial, name='get_product_list_partial'),
    path('manage/product/<int:pk>/', manage.get_manage_product_panel_partial, name='get_product_panel_partial'),
    path('manage/option-type/<int:pk>/', manage.get_manage_option_type_panel_partial, name='get_manage_option_type_panel_partial'),


    # Admin: OptionType CRUD

    path('manage/product/<int:product_pk>/option-type/create/', manage.create_option_type, name='create_option_type'),
    path('manage/option-type/<int:pk>/update/', manage.update_option_type, name='update_option_type'),
    path('manage/option-type/<int:pk>/delete/', manage.delete_option_type, name='delete_option_type'),


    # Admin: OptionValue CRUD
    path('manage/option-type/<int:option_type_pk>/value/create/', manage.create_option_value, name='create_option_value'),
    path('manage/option-value/<int:pk>/update/', manage.update_option_value, name='update_option_value'),
    path('manage/option-value/<int:pk>/delete/', manage.delete_option_value, name='delete_option_value'),


    # Admin: Variant CRUD
    path('manage/product/<int:product_pk>/variant/create/', manage.create_variant, name='create_variant'),
    path('manage/variant/<int:pk>/delete/', manage.delete_variant, name='delete_variant'),


    # Cart
    path('cart/add/<slug:variant_slug>/', cart.add_variant_to_cart, name='add_to_cart'),
    path('cart/add/by-options/<slug:product_slug>/', cart.add_to_cart_by_options, name='add_to_cart_by_options'),
    path('cart/update/<int:variant_id>/', cart.set_cart_quantity, name='set_cart_quantity'),
    path('cart/remove/<int:variant_id>/', cart.remove_from_cart, name='remove_from_cart'),
    path('cart/', cart.view_cart, name='view_cart'),


    # Checkout flow
    path('checkout/details/', checkout.checkout_details, name='checkout_details'),
    path('checkout/details/submit', checkout.checkout_details_submit, name='checkout_details_submit'),
    path('checkout/review/', checkout.checkout_review, name='checkout_review'),
    path('checkout/create/', checkout.checkout_create_order, name='checkout_create_order'),
    path('checkout/resume/', checkout.checkout_resume, name='checkout_resume'),
    path('order/<int:order_id>/thank-you/', checkout.order_thank_you, name='order_thank_you'),

    path('checkout/pay/<int:order_id>/', checkout.checkout_pay, name='checkout_pay'),

    # Email confirmation
    path('checkout/confirm/<str:token>/', checkout.email_confirmation_process_response, name='email_confirmation_process_response'),
    path('checkout/check-confirmed/', checkout.email_confirmation_status, name='email_confirmation_status'),
    path('checkout/resend_confirmation/', checkout.email_confirmation_resend, name='email_confirmation_resend'),
    path('checkout/email_confirmation_success/', checkout.email_confirmation_success, name='email_confirmation_success'),

    # -------------------------------------------------------------------------
    # Legacy / commented routes below still reference `views.*` but are commented
    # so they won't break even though we're no longer importing `views` directly.
    # -------------------------------------------------------------------------

    # path("shop/", views.shop_product_list, name="product_list"),                                  # SSR
    # path("shop/partial/products", views.shop_product_list_partial, name="product_list_partial"),  # HTMX
    # path("api/shop/products", views.api_shop_products, name="api_products"),                      # JSON
    #
    # path("shop/<slug:product_slug>/", views.shop_product_detail, name="product_detail"),          # SSR
    # path("shop/partial/<slug:product_slug>/variants", views.shop_variants_partial, name="variants_partial"),  # HTMX
    # path("api/shop/products/<slug:product_slug>", views.api_shop_product_detail, name="api_product_detail"),  # JSON
    #
    # # Variants
    # path("shop/<slug:product_slug>/<slug:variant_slug>/", views.shop_variant_detail, name="variant_detail"),  # SSR
    # path("shop/partial/<slug:product_slug>/<slug:variant_slug>/card", views.shop_variant_card_partial, name="variant_card_partial"),  # HTMX
    # path("api/shop/products/<slug:product_slug>/variants/<slug:variant_slug>", views.api_shop_variant_detail, name="api_variant_detail"),  # JSON
    #
    # # Optional: quick inventory lookup by SKU
    # path("api/shop/inventory/<str:sku>", views.api_inventory_by_sku, name="api_inventory_by_sku"),
    #
    # path('product/add/<str:encoded_name>/', views.add_product, name='add_product'),
    # path('product/remove/<str:encoded_name>/', views.remove_product, name='remove_product'),
    # path('product/update/<str:encoded_name>/', views.update_product, name='update_product'),
    # path('product/detail/<str:encoded_name>/', views.product_detail, name='product_detail'),
    # path('product/gallery/', views.product_gallery, name='product_gallery'),
    # path('cart/clear/', views.clear_cart, name='cart_clear'),
    # path('cart/detail/', views.cart_detail, name='cart_detail'),
    # path('cart/checkout/', views.checkout, name='checkout'),
    # path('cart/counter/', views.cart_counter, name='cart_counter'),
]
