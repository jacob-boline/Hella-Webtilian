# hr_shop/models.py

from django.contrib.postgres.validators import MinValueValidator
from django.db import models
from django.conf import settings
from hr_access.models import User


def max_per_purchase(product):
    if product.on_hand >= 10:
        return 10
    elif product.on_hand < 10:
        return product.on_hand


class Product(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='products/')


class Price(models.Model):
    pass


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    email = models.EmailField()
    shipping_address = models.ForeignKey('common.Address', on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=[('pending','Pending'),('paid','Paid'),('failed','Failed'),('refunded','Refunded')])
    stripe_customer_id = models.CharField(max_length=64, blank=True, null=True)
    stripe_checkout_session_id = models.CharField(max_length=64, unique=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
