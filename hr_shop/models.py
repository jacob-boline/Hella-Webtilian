# hr_shop/models.py

"""
===========================================
Hella Reptilian Shop Models — Quick Summary
===========================================

Product:
    A sellable catalog item (e.g., SHIRT, ALBUM) that groups one or more variants.

ProductVariant:
    A purchasable variation of a product (e.g., Red XL Shirt) with its own SKU, price,
    and active flag; optionally marked as the product’s primary/default variant to
    display in the shop.

ProductOptionType:
    A per-product attribute category (e.g., Size, Color); may be cloned from an
    OptionTypeTemplate and may contain multiple ProductOptionValues.
    It also carries a drives_image flag telling the UI whether changing this option
    should cause the product image to change.

ProductOptionValue:
    A specific value belonging to an option type (e.g., XL, Black); may be cloned from
    an OptionValueTemplate; used to construct variant combinations.

OptionTypeTemplate:
    A reusable, product-agnostic definition of an attribute type (e.g., “Size”) that
    can be cloned onto products when creating/editing them.

OptionValueTemplate:
    A reusable, product-agnostic definition of an attribute value (e.g., “XL”) that is
    cloned into ProductOptionTypes derived from templates.

ProductImage:
    A reusable image row. Multiple variants can reference the same ProductImage.

ProductVariantOption:
    The join table linking a ProductVariant to the specific ProductOptionValues that
    define its configuration (e.g., Variant #12 → Size: XL, Color: Black).
"""

from decimal import Decimal
from functools import cached_property

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Min, Q
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

from hr_common.db.fields import NormalizedEmailField
from hr_common.db.slug import sync_slug_from_source
from hr_common.models import Address
from hr_common.utils.email import normalize_email


def max_per_purchase(product):
    # NOTE: This helper expects `product.on_hand`, which does not exist on Product yet
    if getattr(product, "on_hand", 0) >= 10:
        return 10
    return max(getattr(product, "on_hand", 0), 0)


# ==========================
# Catalog core
# ==========================


class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        sync_slug_from_source(self, self.name)
        super().save(*args, **kwargs)

    @property
    def display_variant(self):
        """
        Returns the display variant if set, otherwise the first variant available.
        """
        display_variant = self.variants.filter(is_display_variant=True).first()
        if display_variant:
            return display_variant
        return self.variants.order_by("id").first()

    @property
    def display_price(self):
        dv = self.display_variant
        return dv.price if dv else None

    @property
    def min_variant_price(self):
        return self.variants.aggregate(min_price=Min("price"))["min_price"] or None


# ==========================
# Product option types/values
# ==========================


class ProductOptionType(models.Model):
    """
    Per-product attribute type: e.g. Size, Color, Format.
    """

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="option_types")
    name = models.CharField(max_length=64)
    code = models.SlugField()
    position = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    # does this option affect the display image?
    drives_image = models.BooleanField(default=False, help_text=("If true, different values of this option type are expected to " "map to different images for this product."))

    # default selection to pre-populate selects in the UI
    default_value = models.ForeignKey("ProductOptionValue", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        unique_together = [("product", "code")]
        ordering = ["position", "id"]

    def save(self, *args, **kwargs):
        # Autopopulate position if blank/zero, compacting gaps per product.
        if self.position in (0, None):
            existing = ProductOptionType.objects.filter(product=self.product).exclude(id=self.id).values_list("position", flat=True)
            used = set(existing)
            pos = 1
            while pos in used:
                pos += 1
            self.position = pos

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {self.name}"


class ProductOptionValue(models.Model):
    """
    Per-product value for a given option type: e.g. Black, Purple, XL, Vinyl.
    """

    option_type = models.ForeignKey(ProductOptionType, on_delete=models.CASCADE, related_name="values")
    name = models.CharField(max_length=50)  # e.g. 'Black', 'XL'
    code = models.SlugField()
    position = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("option_type", "code")]
        ordering = ["position", "id"]

    def save(self, *args, **kwargs):
        # Autopopulate position if blank/zero, compacting gaps per option_type.
        if self.position in (0, None):
            existing = ProductOptionValue.objects.filter(option_type=self.option_type).exclude(id=self.id).values_list("position", flat=True)
            used = set(existing)
            pos = 1
            while pos in used:
                pos += 1
            self.position = pos

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.option_type.name}: {self.name}"


# ==========================
# Reusable templates
# ==========================


class OptionTypeTemplate(models.Model):
    """
    Reusable option type definition, e.g. 'Size', 'Color', 'Cut'.
    Not tied to a product. Use active=True to show it in the template picker.
    """

    name = models.CharField(max_length=50)
    code = models.SlugField()
    position = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("code",)]
        ordering = ["position", "id"]

    def __str__(self):
        return f"Template: {self.name}"

    def clone_to_product(self, product, *, include_values=True, code_suffix=None):
        """
        Create a ProductOptionType + ProductOptionValue set for this product,
        using this template as the source.
        """
        new_code = self.code
        if code_suffix:
            new_code = f"{self.code}-{code_suffix}"

        base_code = new_code
        counter = 1
        while ProductOptionType.objects.filter(product=product, code=new_code).exists():
            counter += 1
            new_code = f"{base_code}-{counter}"

        new_type = ProductOptionType.objects.create(product=product, name=self.name, code=new_code, position=0, active=True)  # save() will autoincrement position per product

        if include_values:
            templates = self.values.all()
            new_values = []
            for v in templates:
                new_values.append(ProductOptionValue(option_type=new_type, name=v.name, code=v.code, position=0, active=v.active))  # save() will autoincrement
            ProductOptionValue.objects.bulk_create(new_values)

        return new_type


class OptionValueTemplate(models.Model):
    """
    Reusable option value definition, e.g. 'S', 'M', 'L', 'Black', 'Purple'.
    Tied to an OptionTypeTemplate.
    """

    option_type = models.ForeignKey(OptionTypeTemplate, on_delete=models.CASCADE, related_name="values")
    name = models.CharField(max_length=50)
    code = models.SlugField()
    position = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("option_type", "code")]
        ordering = ["position", "id"]

    def __str__(self):
        return f"{self.option_type.name} (template): {self.name}"


# ==========================
# Images
# ==========================


class ProductImage(models.Model):
    """
    A reusable image. One ProductImage can be shared by many variants.
    """

    image = models.ImageField(upload_to="variants/")
    alt_text = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.alt_text or self.image.name


# ==========================
# Variants
# ==========================


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    sku = models.CharField(max_length=64, unique=True)
    slug = models.SlugField(max_length=160, blank=True, unique=True)
    name = models.CharField(max_length=128)

    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])

    is_display_variant = models.BooleanField(default=False, help_text=("If set, this variant will be used as the product default/" "display variant."))

    option_values = models.ManyToManyField(ProductOptionValue, through="ProductVariantOption", related_name="variants", blank=True)

    active = models.BooleanField(default=True)

    image = models.ForeignKey(ProductImage, related_name="variants", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["product", "slug"], name="uq_variant_slug_per_product"),
            models.UniqueConstraint(fields=["product"], condition=Q(is_display_variant=True), name="uq_primary_variant_per_product"),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    def save(self, *args, **kwargs):
        source = f"{self.product.name} {self.name}" if self.product_id and self.name else None
        sync_slug_from_source(self, source, max_length=160)
        super().save(*args, **kwargs)

    @cached_property
    def option_value_ids_set(self):
        return set(self.option_values.values_list("id", flat=True))

    def resolve_image(self):
        """
        Return the best ProductImage for this variant, or None.
        """
        if self.image:
            return self.image
        return None


class ProductVariantOption(models.Model):
    """
    Join: Variant <-> OptionValue (e.g. this variant is Size=XL, Color=Black).
    """

    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="variant_options")
    option_value = models.ForeignKey(ProductOptionValue, on_delete=models.CASCADE, related_name="variant_options")

    class Meta:
        unique_together = [("variant", "option_value")]

    def __str__(self):
        return f"{self.variant} / {self.option_value}"


# ==========================
# Inventory
# ==========================


class InventoryItem(models.Model):
    variant = models.OneToOneField(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="inventory",
    )
    on_hand = models.PositiveIntegerField(default=0)
    reserved = models.PositiveIntegerField(default=0)

    @property
    def available(self):
        return max(self.on_hand - self.reserved, 0)

    def __str__(self):
        return f"{self.variant.sku} - {self.on_hand} on hand"


class Price(models.Model):
    # Placeholder for future pricing models (sales, tiers, etc.)
    pass


# ==========================
# Orders & Customers
# ==========================


class Customer(models.Model):
    email: str
    email = NormalizedEmailField(blank=False, null=False, unique=True, db_index=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, blank=True, null=True, related_name="customer", on_delete=models.SET_NULL)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    middle_initial = models.CharField(max_length=5, null=True, blank=True)
    suffix = models.CharField(max_length=20, null=True, blank=True)
    phone = PhoneNumberField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    wants_saved_info = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["stripe_customer_id"], condition=Q(stripe_customer_id__isnull=False), name="uniq_customer_stripe_customer_id_not_null")]

    def __str__(self):
        label = f"{self.first_name} {self.last_name}".strip() or self.email
        return f"Customer {self.pk} - {label}"

    @property
    def full_name(self):
        parts = [self.first_name, self.middle_initial, self.last_name, self.suffix]

        return " ".join(p for p in parts if p).strip()


class CustomerAddress(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="addresses")
    address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name="customer_links")
    is_default_shipping = models.BooleanField(default=False)
    is_default_billing = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["customer", "address"], name="uq_customer_address"),
            models.UniqueConstraint(fields=["customer"], condition=Q(is_default_shipping=True), name="uq_one_default_shipping_per_customer"),
            models.UniqueConstraint(fields=["customer"], condition=Q(is_default_billing=True), name="uq_one_default_billing_per_customer"),
        ]


# Not currently used, but would like to replace STATUS_CHOICES with this.
class OrderStatus(models.TextChoices):
    RECEIVED = "received"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"


class PaymentStatus(models.TextChoices):
    PENDING = "pending"
    UNPAID = "unpaid"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class Order(models.Model):
    customer = models.ForeignKey(Customer, null=False, blank=False, on_delete=models.PROTECT, related_name="account_get_orders")

    # Order.user is the per-order ownership field (separate from Customer.user),
    # so users can claim or ignore older guest account_get_orders tied to the same email.
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="account_get_orders")

    email: str
    email = NormalizedEmailField(db_index=True)

    stripe_checkout_session_id = models.CharField(max_length=255, blank=True, null=True)

    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)

    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)

    order_status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.RECEIVED)
    shipping_address = models.ForeignKey(Address, on_delete=models.PROTECT, null=True, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    note = models.CharField(max_length=1000, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["stripe_checkout_session_id"], condition=Q(stripe_checkout_session_id__isnull=False), name="uniq_order_stripe_checkout_session_id_not_null"
            ),
            models.UniqueConstraint(fields=["stripe_payment_intent_id"], condition=Q(stripe_payment_intent_id__isnull=False), name="uniq_order_stripe_payment_intent_id_not_null"),
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return f"Order {self.id} ({self.order_status})"

    def can_edit_shipping(self) -> bool:
        return self.payment_status in (PaymentStatus.PENDING, PaymentStatus.FAILED, PaymentStatus.UNPAID)

    def set_shipping_address(self, address: Address):
        if not self.can_edit_shipping():
            raise ValueError("Cannot change address for a non-editable order.")
        self.shipping_address = address
        self.save(update_fields=["shipping_address", "updated_at"])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.quantity} x {self.variant.sku}"


# ==========================
# Email Confirmation
# ==========================


class ConfirmedEmail(models.Model):
    """
    Tracks email addresses that have been confirmed for checkout.
    Once an email is confirmed, it never needs to be confirmed again.
    This enables guest checkout while preventing abuse.
    """

    email: str
    email = NormalizedEmailField(unique=True, db_index=True)
    confirmed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Confirmed Email"
        verbose_name_plural = "Confirmed Emails"
        ordering = ["-confirmed_at"]

    def __str__(self):
        return self.email

    @classmethod
    def is_confirmed(cls, email: str) -> bool:
        """Check if an email address has been confirmed."""
        return cls.objects.filter(email__iexact=normalize_email(email)).exists()

    @classmethod
    def mark_confirmed(cls, email: str) -> "ConfirmedEmail":
        """Mark an email address as confirmed. Idempotent."""
        obj, _ = cls.objects.get_or_create(email=(normalize_email(email)))
        return obj


# To store session state to restore from when a validation link is used from a browser without an active session
# so users aren't redirected to an empty cart after validating.
class CheckoutDraft(models.Model):
    email: str
    email = NormalizedEmailField(db_index=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    address = models.ForeignKey(Address, on_delete=models.PROTECT)
    note = models.CharField(max_length=1000, blank=True, null=True)
    cart = models.JSONField(default=list)  # [{'variant_id': 123, 'qty': 2, 'unit_price': '19.99'}, ...]
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    used_at = models.DateTimeField(null=True, blank=True)
    order = models.OneToOneField("Order", on_delete=models.SET_NULL, null=True, blank=True, related_name="checkout_draft")

    class Meta:
        indexes = [models.Index(fields=["email", "used_at"]), models.Index(fields=["customer", "used_at"])]

        constraints = [models.UniqueConstraint(fields=["customer"], condition=Q(used_at__isnull=True), name="uq_one_active_draft_per_customer")]

    def is_valid(self):
        return self.used_at is None and timezone.now() < self.expires_at
