from django.contrib.postgres.validators import MinValueValidator
from django.db import models

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