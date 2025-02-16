import uuid

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from hr_shop.models import Product


class AddressUsage(models.TextChoices):
    BILLING = 'Billing'
    SHIPPING = 'Shipping'
    RETURN = 'Return'
    RECEIVE = 'Receive'


class Address(models.Model):
    recipient = models.CharField(max_length=150, blank=False, null=False)
    street_number = models.CharField(max_length=150, blank=False, null=False)
    unit = models.CharField(max_length=10, blank=True, null=True)
    city = models.CharField(max_length=100, blank=False, null=False)
    subdivision = models.CharField(max_length=100, blank=False, null=False)
    index = models.CharField(max_length=50, null=False, blank=False, verbose_name="Zip Code")
    country = models.CharField(max_length=3, null=False, blank=False, verbose_name="3 Letter ISO Country Code")

    class Meta:
        abstract = True
        ordering = ('-pk',)

    def __str__(self):
        pass


class BillingAddress(Address):

    def __str__(self):
        return f"{self.recipient}\n{self.street_number} {self.city}, {self.subdivision}\n {self.index} {self.country}"


class MailingAddress(Address):

    def __str__(self):
        return f"{self.recipient}\n{self.street_number} {self.city}, {self.subdivision}\n {self.index} {self.country}"


class OrderStatus(models.TextChoices):
    PROCESSING = 'Processing'
    CANCELLED = 'Cancelled'
    SHIPPED = 'Shipped'
    RETURNED = 'Returned'
    COMPLETE = 'Complete'


class Order(models.Model):
    cart_id = models.CharField(unique=True, blank=False, null=False, max_length=255)
    order_id = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    mailing_address = models.ForeignKey(MailingAddress, on_delete=models.PROTECT)
    billing_address = models.ForeignKey(BillingAddress, blank=True, null=True, on_delete=models.PROTECT)
    status = models.CharField(choices=OrderStatus.choices, max_length=50)
    subtotal = models.PositiveIntegerField(validators=[MinValueValidator(50), MaxValueValidator(999999)])
    tax = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(999999)])
    grand_total = models.PositiveIntegerField(blank=False, null=False, validators=[MinValueValidator(50), ])
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'<Order: {self.order_id}'

    def update_status(self, new_status):
        if new_status in OrderStatus.choices:
            self.status = new_status
            message = f'Order status updated to {self.status}'
            return message


class OrderLine(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_lines')
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='items')
    standing_unit_price = models.PositiveIntegerField(verbose_name="Price at time of order")
    quantity = models.PositiveSmallIntegerField()

    def __str__(self):
        return f'<OrderLine: {self.product.name} (x{self.quantity}) @ ${self.standing_unit_price/100}, Order ID: {self.order.id}>'

    @property
    def subtotal(self):
        return self.standing_unit_price * self.quantity
