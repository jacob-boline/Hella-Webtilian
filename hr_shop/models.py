# hr_shop/models.py

from decimal import Decimal

from django.conf import settings
from django.contrib.postgres.validators import MinValueValidator
from django.core.validators import EmailValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from hr_common.models import Address
from hr_core.utils.slug import sync_slug_from_source


def max_per_purchase(product):
    if product.on_hand >= 10:
        return 10
    elif product.on_hand < 10:
        return product.on_hand


class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        sync_slug_from_source(self, self.name)
        super().save(*args, **kwargs)

    @property
    def display_variant(self):
        """
        Returns the primary variant if set, otherwise the first variant available.
        """
        primary = self.variants.filter(is_primary=True).first()
        if primary:
            return primary
        return self.variants.order_by('id').first()

    @property
    def display_price(self):
        dv = self.display_variant
        return dv.price if dv else None

    @property
    def min_variant_price(self):
        prices = [v.price for v in self.variants.all()]
        return min(prices) if prices else None


class ProductOptionType(models.Model):
    """
    Per-product attribute type: e.g. Size, Color, Format
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='option_types', )
    name = models.CharField(max_length=50)  # e.g. 'Size'
    code = models.SlugField(max_length=50)  # e.g. 'size', 'color', 'format'
    position = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [('product', 'code')]
        ordering = ['position', 'id']

    def __str__(self):
        return f'{self.product.name} - {self.name}'


class ProductOptionValue(models.Model):
    """
    Per-product value for a given option type: e.g. Black, Purple, XL, Vinyl
    """
    option_type = models.ForeignKey(ProductOptionType, on_delete=models.CASCADE, related_name='values')
    name = models.CharField(max_length=50)  # e.g. 'Black', 'XL'
    code = models.SlugField(max_length=50)  # e.g. 'black', 'xl'
    position = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [('option_type', 'code')]
        ordering = ['position', 'id']

    def __str__(self):
        return f'{self.option_type.name}: {self.name}'


class ProductVariant(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='variants')
    sku = models.CharField(max_length=64, blank=False, null=False, unique=True)
    slug = models.SlugField(max_length=160, blank=True)
    name = models.CharField(max_length=128)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0'))])
    is_primary = models.BooleanField(default=False, help_text="If set, this variant will be used as the product default/display variant.")
    option_values = models.ManyToManyField(ProductOptionValue, through='ProductVariantOption', related_name='variants', blank=True)

    # size = model.CharField(max_length=16, blank=True, choices=[
    #     ('XS', 'XS'),
    #     ('S', 'S'),
    #     ('M', 'M'),
    #     ('L', 'L'),
    #     ('XL', 'XL'),
    #     ('2XL', '2XL'),
    # ])

    # color = models.CharField(max_length=32, blank=True, choices=[])


    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['product', 'slug'], name='uq_variant_slug_per_product'),
            models.UniqueConstraint(fields=['product'], condition=Q(is_primary=True), name='uq_primary_variant_per_product',),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    def save(self, *args, **kwargs):
        source = f'{self.product.name} {self.name}' if self.product_id and self.name else None
        sync_slug_from_source(self, source, max_length=160)
        super().save(*args, **kwargs)


class ProductVariantOption(models.Model):
    """
    Join: Variant <-> OptionValue (e.g. this variant is Size=XL, Color=Black).
    """
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='variant_options')
    option_value = models.ForeignKey(ProductOptionValue, on_delete=models.CASCADE, related_name='variant_options')

    class Meta:
        unique_together = [('variant', 'option_value')]

    def __str__(self):
        return f'{self.variant} / {self.option_value}'


class InventoryItem(models.Model):
    variant = models.OneToOneField(ProductVariant, on_delete=models.CASCADE, related_name="inventory")
    on_hand = models.PositiveIntegerField(default=0)
    reserved = models.PositiveIntegerField(default=0)

    @property
    def available(self):
        return max(self.on_hand - self.reserved, 0)

    def __str__(self):
        return f"{self.variant.sku} - {self.on_hand} on hand"


class Price(models.Model):
    pass

class Customer(models.Model):
    email = models.EmailField(blank=False, null=False, unique=False, validators=[EmailValidator()])
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, related_name='customers', on_delete=models.SET_NULL)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('email',)]
        ordering = ['-created_at']

    def __str__(self):
        label = f'{self.first_name} {self.last_name}'.strip() or self.email
        return f'Customer {self.pk} - {label}'


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    ]

    # user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='orders',)
    customer = models.ForeignKey(Customer, null=True, blank=False, on_delete=models.PROTECT, related_name='orders')
    stripe_checkout_session_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    email = models.EmailField(null=False, blank=False, validators=[EmailValidator()])
    shipping_address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} ({self.status})"

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().casefold()
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.quantity} x {self.variant.sku}"


class WebhookEvent(models.Model):
    event_id = models.CharField(max_length=255, unique=True)
    type = models.CharField(max_length=255)
    payload = models.JSONField()
    received_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)
    ok = models.BooleanField(default=False)


