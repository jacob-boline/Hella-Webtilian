# hr_core/utils/slug.py

import itertools
from typing import Optional
from django.utils.text import slugify
from django.db.models import Model


def generate_unique_slug(instance, value, slug_field_name='slug', max_length=220):
    """
        Generate a unique slug for a model instance.

        Args:
            instance:  The model instance to assign the slug to.
            value:     The raw string to slugify (e.g., title, name, date+venue).
            slug_field_name:  The name of the slug field (default: 'slug').
            max_length: The max length allowed for the slug (default: 220).

        Returns:
            A unique slug string.
        """
    if not isinstance(instance, Model):
        raise TypeError("instance must be a Django model.")

    base_slug = slugify(value) or "item"
    if max_length:
        base_slug = base_slug[:max_length]

    model = instance.__class__
    slug_candidate = base_slug
    for i in itertools.count(2):
        exists = model.objects.filter(**{slug_field_name: slug_candidate}).exclude(pk=instance.pk).exists()
        if not exists:
            return slug_candidate
        suffix = f"-{i}"
        cutoff = max_length - len(suffix)
        slug_candidate = f"{base_slug[:cutoff]}{suffix}"


def sync_slug_from_source(instance, source_value: str, *, slug_field_name: str = 'slug', allow_update: bool = True, max_length: int = 220) -> None:
    """
    Ensure instance.<slug_field_name> is set from 'source_value' IF:
      - On create and slug is blank, OR
      - On update and 'allow_update' is True AND slug still appears auto-generated.

    This compares to the original instance to decide whether slug looks "manual".
    """

    if not source_value:
        return

    current_slug: Optional[str] = getattr(instance, slug_field_name, None)

    # CREATE
    if not instance.pk:
        if not current_slug:
            setattr(instance, slug_field_name, generate_unique_slug(instance, source_value, slug_field_name, max_length))
        return

    # UPDDATE
    ModelClass = instance.__class__
    try:
        original = ModelClass.objects.only(slug_field_name).get(pk=instance.pk)
    except ModelClass.DoesNotExist:
        original = None

    if not original:
        if not current_slug:
            setattr(instance, slug_field_name, generate_unique_slug(instance, source_value, slug_field_name, max_length))
        return

    original_slug = getattr(original, slug_field_name, '') or ''

    if not allow_update:
        if not current_slug:
            setattr(instance, slug_field_name, generate_unique_slug(instance, source_value, slug_field_name, max_length))
        return

    auto_from_current = generate_unique_slug(instance, source_value, slug_field_name, max_length)

    looks_auto = (current_slug == auto_from_current) or (current_slug == original_slug)

    if not current_slug or looks_auto:
        setattr(instance, slug_field_name, generate_unique_slug(instance, source_value, slug_field_name, max_length))
