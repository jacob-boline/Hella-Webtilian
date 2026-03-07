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
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Count, Min, Prefetch, Q
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

from hr_common.db.fields import NormalizedEmailField
from hr_common.db.slug import sync_slug_from_source
from hr_common.models import Address
from hr_common.utils.email import normalize_email


class Activatable(models.Model):
    active = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def deactivate(self, *, save: bool = True, cascade: bool = True) -> None:
        self.active = False
        if save:
            self.save(update_fields=["active"])
        if not cascade:
            return

    def activate(self, *, save: bool = True, cascade: bool = True) -> None:
        self.active = True
        if save:
            self.save(update_fields=["active"])


#     __   __   __   __        __  ___
#    |__) |__) /  \ |  \ |  | /  `  |
#    |    |  \ \__/ |__/ \__/ \__,  |
#
class Product(Activatable):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True, default="")
    active = models.BooleanField(default=False)
    default_image = models.ForeignKey("ProductImage", related_name="products", null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        sync_slug_from_source(self, self.name)
        super().save(*args, **kwargs)

    def deactivate(self, *, save: bool = True, cascade: bool = True) -> None:
        """ Product deactivation cascades to variants + option types + option values. """
        super().deactivate(save=save, cascade=cascade)
        if not cascade:
            return

        self.variants.update(active=False)
        self.option_types.update(active=False)
        ProductOptionValue.objects.filter(option_type__product=self).update(active=False)

    @property
    def display_variant(self):
        """ Returns the display variant if set, otherwise the first variant available. """
        qs = self.variants.filter(active=True)
        display_variant = qs.filter(is_display_variant=True).first()
        if display_variant:
            return display_variant
        return qs.order_by("id").first()

    @property
    def display_price(self):
        dv = self.display_variant
        return dv.price if dv else None

    @property
    def min_variant_price(self):
        return self.variants.filter(active=True).aggregate(min_price=Min("price"))["min_price"]


#     __   __  ___    __          ___      __   ___
#    /  \ |__)  |  | /  \ |\ |     |  \ / |__) |__
#    \__/ |     |  | \__/ | \|     |   |  |    |___
#
class ProductOptionType(Activatable):
    """ Per-product attribute type: e.g. Size, Color, Format. """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="option_types")
    name = models.CharField(max_length=64)
    code = models.SlugField()
    position = models.PositiveIntegerField(default=0)
    # does this option affect the display image?
    drives_image = models.BooleanField(default=False, help_text=("If true, different values of this option type are expected to map to different images for this product."))
    # default selection to pre-populate selects in the UI
    default_value = models.ForeignKey("ProductOptionValue", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(fields=["product", "code"], name="uniq_together_product_option_type__product_code"),
            models.UniqueConstraint(fields=["product", "name"], name="uniq_together_product_option_type__product_name")
        ]

    def deactivate(self, *, save: bool = True, cascade: bool = True) -> None:
        """ OptionType deactivation cascades to its values. """
        super().deactivate(save=save, cascade=cascade)
        if cascade:
            self.values.update(active=False)

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

    def clean(self):
        super().clean()
        if self.default_value_id:
            if self.default_value.option_type.product_id != self.product_id:
                raise ValidationError({
                    "default_value": "Default value must belong to this product."
                })

            if self.pk and self.default_value.option_type_id != self.pk:
                raise ValidationError({
                    "default_value": "Default value must belong to this option type."
                })


#     __   __  ___    __                               ___
#    /  \ |__)  |  | /  \ |\ |    \  /  /\  |    |  | |__
#    \__/ |     |  | \__/ | \|     \/  /~~\ |___ \__/ |___
#
class ProductOptionValue(Activatable):
    """ The associated values to a ProductOptionType -- e.g. type:size, values:s,m,lg """
    option_type = models.ForeignKey(ProductOptionType, on_delete=models.CASCADE, related_name="values")
    name = models.CharField(max_length=50)  # e.g. 'Black', 'XL'
    code = models.SlugField()
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(fields=["option_type", "code"], name="uniq_together_product_option_value__option_type_code")
        ]

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


#     __   __  ___    __          ___      __   ___    ___  ___        __            ___  ___
#    /  \ |__)  |  | /  \ |\ |     |  \ / |__) |__      |  |__   |\/| |__) |     /\   |  |__
#    \__/ |     |  | \__/ | \|     |   |  |    |___     |  |___  |  | |    |___ /~~\  |  |___
#
class OptionTypeTemplate(Activatable):
    """
    Reusable option type definition, e.g. 'Size', 'Color', 'Cut'.
    Not tied to a product. Use active=True to show it in the template picker.
    """

    name = models.CharField(max_length=50)
    code = models.SlugField(unique=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return f"Template: {self.name}"

    def clone_to_product(self, product, *, include_values=True, code_suffix=None):
        """ Create a ProductOptionType + ProductOptionValue set for this product, using this template as the source. """
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
            for template_value in self.values.all().order_by("position", "id"):
                ProductOptionValue.objects.create(
                    option_type=new_type,
                    name=template_value.name,
                    code=template_value.code,
                    position=0,
                    active=template_value.active
                )

        return new_type


#     __   __  ___    __                               ___    ___  ___        __            ___  ___
#    /  \ |__)  |  | /  \ |\ |    \  /  /\  |    |  | |__      |  |__   |\/| |__) |     /\   |  |__
#    \__/ |     |  | \__/ | \|     \/  /~~\ |___ \__/ |___     |  |___  |  | |    |___ /~~\  |  |___
#
class OptionValueTemplate(Activatable):
    """
    Reusable option value definition, e.g. 'S', 'M', 'L', 'Black', 'Purple'.
    Tied to an OptionTypeTemplate.
    """
    option_type = models.ForeignKey(OptionTypeTemplate, on_delete=models.CASCADE, related_name="values")
    name = models.CharField(max_length=50)
    code = models.SlugField()
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(fields=["option_type", "code"], name="uniq_together_opt_val_temp__option_type_code")
        ]

    def __str__(self):
        return f"{self.option_type.name} (template): {self.name}"


#     __   __   __   __        __  ___                  __   ___
#    |__) |__) /  \ |  \ |  | /  `  |     |  |\/|  /\  / _` |__
#    |    |  \ \__/ |__/ \__/ \__,  |     |  |  | /~~\ \__> |___
#
class ProductImage(models.Model):
    """ A reusable image. One ProductImage can be shared by many variants. """
    image = models.ImageField(upload_to="variants/")
    alt_text = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.alt_text or self.image.name


#               __              ___     __        ___  __          __   ___ ___
#    \  /  /\  |__) |  /\  |\ |  |     /  \ |  | |__  |__) \ /    /__` |__   |
#     \/  /~~\ |  \ | /~~\ | \|  |     \__X \__/ |___ |  \  |     .__/ |___  |
#
# noinspection PyTypeChecker
class ProductVariantQuerySet(models.QuerySet["ProductVariant"]):
    def with_orders_or_inventory(self) -> "ProductVariantQuerySet":
        return self.filter(
            Q(orderitem_set__isnull=False) | Q(inventory__isnull=False)
        )


class ProductVariantManager(models.Manager.from_queryset(ProductVariantQuerySet)):
    pass


#               __              ___
#    \  /  /\  |__) |  /\  |\ |  |
#     \/  /~~\ |  \ | /~~\ | \|  |
#
class ProductVariant(Activatable):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    sku = models.CharField(max_length=64, unique=True)
    slug = models.SlugField(max_length=160, blank=True)
    name = models.CharField(max_length=128)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    is_display_variant = models.BooleanField(default=False, help_text=("If set, this variant will be used as the product default display variant."))
    option_values = models.ManyToManyField(ProductOptionValue, through="ProductVariantOption", related_name="variants", blank=True)
    image = models.ForeignKey(ProductImage, related_name="variants", null=True, blank=True, on_delete=models.SET_NULL)

    objects = ProductVariantManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["product", "slug"], name="uq_variant_slug_per_product"),
            models.UniqueConstraint(fields=["product"], condition=Q(is_display_variant=True), name="uq_primary_variant_per_product")
        ]

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    def save(self, *args, **kwargs):
        source = f"{self.product.name} {self.name}" if self.product_id and self.name else None
        sync_slug_from_source(self, source, max_length=160)
        super().save(*args, **kwargs)

    # Only validates combination state after the variant exists
    # Use in combination with ProductVariantOption.clean()
    #
    # The through-model validation catches individual bad link rows, and this one later catches full-set issues.
    #
    def clean(self):
        super().clean()

        if self.is_display_variant and not self.active:
            raise ValidationError({
                "is_display_variant": "An inactive variant cannot be the display variant."
            })

        if not self.pk:
            return

        option_values = list(self.option_values.select_related("option_type").all())

        wrong_product_values = [
            ov for ov in option_values if ov.option_type.product_id != self.product_id
        ]
        if wrong_product_values:
            bad_names = ", ".join(str(ov) for ov in wrong_product_values[:5])
            raise ValidationError({
                "option_values": f"Some option values belong to a different product than this variant: {bad_names}"
            })

        seen_option_type_ids = set()
        duplicate_type_names = []

        for ov in option_values:
            option_type_id = ov.option_type_id
            if option_type_id in seen_option_type_ids:
                duplicate_type_names.append(ov.option_type.name)
            else:
                seen_option_type_ids.add(option_type_id)

        if duplicate_type_names:
            names = ", ".join(sorted(set(duplicate_type_names)))
            raise ValidationError({
                "option_values": f"Only one value per option type is allowed. Duplicates: {names}"
            })

        if self.pk and self.has_same_option_combination_as_existing():
            raise ValidationError({
                "option_values": "Another variant already uses this exact option combination."
            })

    def validate_option_values(self):
        """
        Explicit validator for callers to run after mutating m2m option values.
        Useful as m2m values are not available during initial save.
        """
        self.clean()

    def has_orders_or_inventory(self) -> bool:
        return ProductVariant.objects.filter(pk=self.pk).with_orders_or_inventory().exists()

    @cached_property
    def option_value_ids_set(self):
        return set(self.option_values.values_list("id", flat=True))

    def resolve_image(self):
        """
        Return the best ProductImage for this variant, or None.
        Variant-specific image always wins over product-level fallback image.
        """
        if self.image:
            return self.image
        if self.product_id and self.product and self.product.default_image:
            return self.product.default_image
        return None

    def has_same_option_combination_as_existing(self) -> bool:
        if not self.pk:
            return False

        own_ids = set(self.option_values.values_list("id", flat=True))
        if not own_ids:
            return False

        number_of_options = len(own_ids)

        sibling_variants = (
            ProductVariant.objects
            .filter(product_id=self.product_id)
            .exclude(pk=self.pk)
            .annotate(option_value_count=Count("option_values", distinct=True))
            .filter(option_value_count=number_of_options)
            .prefetch_related(
                Prefetch("option_values", queryset=ProductOptionValue.objects.only("id"))
            )
        )

        for sibling in sibling_variants:
            sibling_ids = {ov.id for ov in sibling.option_values.all()}
            if sibling_ids == own_ids:
                return True

        return False


#               __              ___     __   __  ___    __
#    \  /  /\  |__) |  /\  |\ |  |     /  \ |__)  |  | /  \ |\ |
#     \/  /~~\ |  \ | /~~\ | \|  |     \__/ |     |  | \__/ | \|
#
class ProductVariantOption(models.Model):
    """ Join: Variant <-> OptionValue (e.g. this variant is Size=XL, Color=Black). """
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="variant_options")
    option_value = models.ForeignKey(ProductOptionValue, on_delete=models.CASCADE, related_name="variant_options")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["variant", "option_value"], name="uniq_together_prod_var_opt__variant_option_value")
        ]

    def __str__(self):
        return f"{self.variant} / {self.option_value}"

    def clean(self):
        super().clean()

        if not self.variant_id or not self.option_value_id:
            return

        variant_product_id = self.variant.product_id
        option_value_product_id = self.option_value.option_type.product_id

        if variant_product_id != option_value_product_id:
            raise ValidationError({
                "option_value": "This option value belongs to a different product than the variant."
            })

        duplicate_type_exists = (
            ProductVariantOption.objects
            .filter(
                variant_id=self.variant_id,
                option_value__option_type_id=self.option_value.option_type_id
            )
            .exclude(pk=self.pk)
            .exists()
        )

        if duplicate_type_exists:
            raise ValidationError({
                "option_value": "This variant already has a value for that option type."
            })

    # bulk updates will bypass this, including the full_clean call
    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


#                 ___      ___  __   __           ___  ___
#    | |\ | \  / |__  |\ |  |  /  \ |__) \ /    |  |  |__   |\/|
#    | | \|  \/  |___ | \|  |  \__/ |  \  |     |  |  |___  |  |
#
class InventoryItem(models.Model):
    variant = models.OneToOneField(ProductVariant, on_delete=models.CASCADE, related_name="inventory")
    on_hand = models.PositiveIntegerField(default=0)
    reserved = models.PositiveIntegerField(default=0)

    @property
    def available(self) -> int:
        return max(self.on_hand - self.reserved, 0)

    def __str__(self):
        return f"{self.variant.sku} - {self.on_hand} on hand"


#     __   __     __   ___
#    |__) |__) | /  ` |__
#    |    |  \ | \__, |___
#
class Price(models.Model):
    # Placeholder for future pricing models (sales, tiers, etc.)
    pass


#     __        __  ___  __         ___  __
#    /  ` |  | /__`  |  /  \  |\/| |__  |__)
#    \__, \__/ .__/  |  \__/  |  | |___ |  \
#
class Customer(models.Model):
    email: str
    email = NormalizedEmailField(max_length=254, unique=True, db_index=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, blank=True, null=True, related_name="customer", on_delete=models.SET_NULL)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    middle_initial = models.CharField(max_length=5, blank=True, default="")
    suffix = models.CharField(max_length=20, blank=True, default="")
    phone = PhoneNumberField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)  #NOSONAR
    wants_saved_info = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["stripe_customer_id"], condition=Q(stripe_customer_id__isnull=False), name="uniq_customer_stripe_customer_id_not_null"),
            models.UniqueConstraint(fields=["phone"], condition=~Q(phone=""), name="uniq_nonblank_customer_phone")
        ]

    def __str__(self):
        label = f"{self.first_name} {self.last_name}".strip() or self.email
        return f"Customer {self.pk} - {label}"

    def save(self, *args, **kwargs):
        if self.stripe_customer_id == "":
            self.stripe_customer_id = None
        super().save(*args, **kwargs)

    @property
    def full_name(self) -> str:
        parts = [self.first_name, self.middle_initial, self.last_name, self.suffix]
        return " ".join(p for p in parts if p).strip()


#     __        __  ___  __         ___  __           __   __   __   ___  __   __
#    /  ` |  | /__`  |  /  \  |\/| |__  |__)     /\  |  \ |  \ |__) |__  /__` /__`
#    \__, \__/ .__/  |  \__/  |  | |___ |  \    /~~\ |__/ |__/ |  \ |___ .__/ .__/
#
class CustomerAddress(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="addresses")
    address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name="customer_links")
    is_default_shipping = models.BooleanField(default=False)
    is_default_billing = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["customer", "address"], name="uq_customer_address"),
            models.UniqueConstraint(fields=["customer"], condition=Q(is_default_shipping=True), name="uq_one_default_shipping_per_customer"),
            models.UniqueConstraint(fields=["customer"], condition=Q(is_default_billing=True), name="uq_one_default_billing_per_customer")
        ]

    def __str__(self):
        return f"Customer ID: {self.customer_id}; Address ID: {self.address_id}"


# Not currently used, but would like to replace STATUS_CHOICES with this.
#     __   __   __   ___  __      __  ___      ___       __
#    /  \ |__) |  \ |__  |__)    /__`  |   /\   |  |  | /__`
#    \__/ |  \ |__/ |___ |  \    .__/  |  /~~\  |  \__/ .__/
#
class OrderStatus(models.TextChoices):
    RECEIVED   = "received"
    PROCESSING = "processing"
    SHIPPED    = "shipped"
    DELIVERED  = "delivered"
    CANCELLED  = "cancelled"
    RETURNED   = "returned"


#     __                  ___      ___     __  ___      ___       __
#    |__)  /\  \ /  |\/| |__  |\ |  |     /__`  |   /\   |  |  | /__`
#    |    /~~\  |   |  | |___ | \|  |     .__/  |  /~~\  |  \__/ .__/
#
class PaymentStatus(models.TextChoices):
    PENDING  = "pending"
    UNPAID   = "unpaid"
    PAID     = "paid"
    FAILED   = "failed"
    REFUNDED = "refunded"


#     __   __   __   ___  __
#    /  \ |__) |  \ |__  |__)
#    \__/ |  \ |__/ |___ |  \
#
class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="orders")
    # Order.user is the per-order ownership field (separate from Customer.user),
    # so users can claim or ignore older guest account_get_orders tied to the same email.
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")
    email: str
    email = NormalizedEmailField(db_index=True, max_length=254)
    stripe_checkout_session_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)  # NOSONAR
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)  # NOSONAR
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    order_status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.RECEIVED)
    shipping_address = models.ForeignKey(Address, on_delete=models.PROTECT, null=True, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    note = models.CharField(max_length=1000, blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["stripe_checkout_session_id"], condition=Q(stripe_checkout_session_id__isnull=False), name="uniq_order_stripe_checkout_session_id_not_null"),
            models.UniqueConstraint(fields=["stripe_payment_intent_id"], condition=Q(stripe_payment_intent_id__isnull=False), name="uniq_order_stripe_payment_intent_id_not_null")
        ]

    def __str__(self):
        return f"Order {self.id} ({self.order_status})"

    def can_edit_shipping(self) -> bool:
        return self.payment_status in (PaymentStatus.PENDING, PaymentStatus.FAILED, PaymentStatus.UNPAID)

    def set_shipping_address(self, address: Address):
        if not self.can_edit_shipping():
            raise ValueError("Cannot change address for a non-editable order.")
        self.shipping_address = address
        self.save(update_fields=["shipping_address", "updated_at"])


#     __   __   __   ___  __       ___  ___
#    /  \ |__) |  \ |__  |__)    |  |  |__   |\/|
#    \__/ |  \ |__/ |___ |  \    |  |  |___  |  |
#
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])

    @property
    def subtotal(self) -> Decimal:
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.quantity} x {self.variant.sku}"


#     __   __        ___    __         ___  __      ___
#    /  ` /  \ |\ | |__  | |__)  |\/| |__  |  \    |__   |\/|  /\  | |
#    \__, \__/ | \| |    | |  \  |  | |___ |__/    |___  |  | /~~\ | |___
#
class ConfirmedEmail(models.Model):
    """
    Tracks email addresses that have been confirmed for checkout.
    Once an email is confirmed, it never needs to be confirmed again.
    This enables guest checkout while preventing abuse.
    """
    email: str
    email = NormalizedEmailField(unique=True, db_index=True, max_length=254)
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
#     __        ___  __        __       ___     __   __        ___ ___
#    /  ` |__| |__  /  ` |__/ /  \ |  |  |     |  \ |__)  /\  |__   |
#    \__, |  | |___ \__, |  \ \__/ \__/  |     |__/ |  \ /~~\ |     |
#
class CheckoutDraft(models.Model):
    email: str
    email = NormalizedEmailField(db_index=True, max_length=254)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    address = models.ForeignKey(Address, on_delete=models.PROTECT)
    note = models.CharField(max_length=1000, blank=True, default="")
    cart = models.JSONField(default=list)  # [{'variant_id': 123, 'qty': 2, 'unit_price': '19.99'}, ...]
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    used_at = models.DateTimeField(null=True, blank=True)
    order = models.OneToOneField("Order", on_delete=models.SET_NULL, null=True, blank=True, related_name="checkout_draft")

    class Meta:
        indexes = [
            models.Index(fields=["email", "used_at"]),
            models.Index(fields=["customer", "used_at"])]
        constraints = [
            models.UniqueConstraint(fields=["customer"], condition=Q(used_at__isnull=True), name="uq_one_active_draft_per_customer")
        ]

    def __str__(self):
        return f"Email: {self.email}; Customer_ID: {self.customer.id}; Created at: {self.created_at}; Expires at: {self.expires_at}; Order ID: {self.order_id or 'None'}"

    def is_valid(self) -> bool:
        return self.used_at is None and timezone.now() < self.expires_at
