# hr_shop/services/customers.py

from django.db import transaction

# from hr_common.utils.email import normalize_email
from hr_shop.models import Customer


# def get_or_create_customer_for_checkout(*, email: str, first_name: str = '', last_name: str = '', user=None) -> Customer:
#     """
#         Resolve or create a Customer for a checkout.
#
#         - Normalize email.
#         - If a Customer exists for that email, reuse it.
#         - If not, create one.
#         - If `user` is passed and Customer.user is empty, attach it.
#         """
#     email = normalize_email(email)
#
#     customer, created = Customer.objects.select_for_update().get_or_create(
#         email=email,
#         defaults={
#             'first_name': first_name or '',
#             'last_name': last_name or '',
#             'user': user if user and user.is_authenticated else None
#         }
#     )
#
#     if user and user.is_authenticated and customer.user_id is None:
#         customer.user = user
#         customer.save(update_fields=['user'])
#
#     return customer


@transaction.atomic
def attach_customer_to_user(user) -> int:
    email = user.email
    if not email:
        return 0

    qs = Customer.objects.filter(email=email, user__isnull=True)
    updated = qs.update(user=user)
    return updated
