# hr_shop/urls.py

from django.urls import path
from hr_shop import views

app_name = 'hr_shop'

urlpatterns = [

# Products

    path('<slug:product_slug>/modal/', views.get_product_modal_partial, name='get_product_modal_partial'),

    path('manage/', views.product_manager, name='product_manager'),

    # Product Management Partials
    path('manage/products/', views.get_manage_product_list_partial, name='get_product_list_partial'),
    path('manage/product/<int:pk>/', views.get_manage_product_panel_partial, name='get_product_panel_partial'),
    path('manage/option-type/<int:pk>/', views.get_manage_option_type_panel_partial, name='get_option_type_panel_partial'),

    # Product CRUD
    path('manage/products/create/', views.product_create, name='product_create'),
    path('manage/product/<int:pk>/update/', views.product_update, name='product_update'),

    # OptionType CRUD
    path('manage/product/<int:product_pk>/option-type/create/', views.create_option_type, name='create_option_type'),
    path('manage/option-type/<int:pk>/update/', views.update_option_type, name='update_option_type'),
    path('manage/option-type/<int:pk>/delete/', views.delete_option_type, name='delete_option_type'),

    # OptionValue CRUD
    path('manage/option-type/<int:option_type_pk>/value/create/', views.create_option_value, name='create_option_value'),
    path('manage/option-value/<int:pk>/update/', views.update_option_value, name='update_option_value'),
    path('manage/option-value/<int:pk>/delete/', views.delete_option_value, name='delete_option_value'),

    # Variant CRUD
    path('manage/product/<int:product_pk>/variant/create/', views.create_variant, name='create_variant'),
    path('manage/variant/<int:pk>/delete/', views.delete_variant, name='delete_variant'),

#     path("shop/", views.shop_product_list, name="product_list"),                                  # SSR
#     path("shop/partial/products", views.shop_product_list_partial, name="product_list_partial"),  # HTMX
#     path("api/shop/products", views.api_shop_products, name="api_products"),                      # JSON
#
#     path("shop/<slug:product_slug>/", views.shop_product_detail, name="product_detail"),          # SSR
#     path("shop/partial/<slug:product_slug>/variants", views.shop_variants_partial, name="variants_partial"),  # HTMX
#     path("api/shop/products/<slug:product_slug>", views.api_shop_product_detail, name="api_product_detail"),  # JSON
#
#     # Variants
#     path("shop/<slug:product_slug>/<slug:variant_slug>/", views.shop_variant_detail, name="variant_detail"),  # SSR
#     path("shop/partial/<slug:product_slug>/<slug:variant_slug>/card", views.shop_variant_card_partial, name="variant_card_partial"),  # HTMX
#     path("api/shop/products/<slug:product_slug>/variants/<slug:variant_slug>", views.api_shop_variant_detail, name="api_variant_detail"),  # JSON
#
#     # Optional: quick inventory lookup by SKU
#     path("api/shop/inventory/<str:sku>", views.api_inventory_by_sku, name="api_inventory_by_sku"),

    path('product/add/<str:encoded_name>/', views.add_product, name='add_product'),
    path('product/remove/<str:encoded_name>/', views.remove_product, name='remove_product'),
    path('product/update/<str:encoded_name>/', views.update_product, name='update_product'),
    path('product/detail/<str:encoded_name>/', views.product_detail, name='product_detail'),
    path('product/gallery/', views.product_gallery, name='product_gallery'),
    path('cart/clear/', views.clear_cart, name='cart_clear'),
    path('cart/detail/', views.cart_detail, name='cart_detail'),
    path('cart/checkout/', views.checkout, name='checkout'),
    path('cart/counter/', views.cart_counter, name='cart_counter'),
]