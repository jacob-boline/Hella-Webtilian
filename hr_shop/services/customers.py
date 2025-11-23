# hr_shop/services/customerw.py

from django.db import transaction
from django.contrib.auth import get_user_model
from hr_shop.models import Order, Customer


def _norm_email(s:str) -> str:
    return (s or '').strip().casefold()


def get_or_create_customer_for_checkout(*, email: str, first_name: str = '', last_name: str = '', user=None) -> Customer:
    """
        Resolve or create a Customer for a checkout.

        - Normalize email.
        - If a Customer exists for that email, reuse it.
        - If not, create one.
        - If `user` is passed and Customer.user is empty, attach it.
        """
    email = _norm_email(email)

    customer, created = Customer.objects.select_for_update().get_or_create(
        email=email,
        defaults={
            'first_name': first_name or '',
            'last_name': last_name or '',
            'user': user if user and user.is_authenticated else None,
        },
    )

    if user and user.is_authenticated and customer.user_id is None:
        customer.user = user
        customer.save(update_fields=['user'])

    return customer


@transaction.atomic
def attach_customer_to_user(user) -> int:
    email = _norm_email(getattr(user, 'email', ''))
    if not email:
        return 0

    qs = Customer.objects.filter(email=email, user__isnull=True)
    updated = qs.update(user=user)
    return updated

#
# def attach_guest_orders_for_user(user) -> int:
#     if not user or not getattr(user, 'email', None):
#         return 0
#     email = user.email.strip().casefold()
#     with transaction.atomic():
#         return Order.objects.filter(user__isnull=True, email=email).update(user=user)


# put the below in the place order flow:
# order = Order.objects.create(
#     user=request.user if request.user.is_authenticated else None,
#     email=(request.user.email if request.user.is_authenticated else guest_email),
#     # ...other fields...
# )
