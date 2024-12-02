from django.urls import path

from hr_shop import views

app_name = 'hr_shop'

urlpatterns = [
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