# hr_about/urls.py

from django.urls import path
from hr_about import views

app_name = 'hr_about'

url_patterns = [
    path('carousel/partial/', views.get_carousel_partial, name='get_carousel_partial'),
    path('quotes/partial/', views.get_quotes_partial, name='get_quotes_partial'),
]