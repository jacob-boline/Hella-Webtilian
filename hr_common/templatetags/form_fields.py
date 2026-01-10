# hr_common/templatetags/form_fields.py


import logging

from django import template
from django.forms import BoundField

from hr_common.logging import log_event

register = template.Library()
logger = logging.getLogger(__name__)


def _field_state(bound_field: BoundField) -> str:
    form_is_bound = getattr(bound_field.form, 'is_bound', False)
    has_errors = bool(bound_field.errors)

    if has_errors:
        return 'error'
    if form_is_bound:
        return 'valid'
    return 'neutral'


@register.inclusion_tag('hr_common/_form_field.html')
def form_field(
        field,
        label=None,
        required=None,
        help=None,
        wrapper_classes="field-row field-row-full",
        group_classes="field-group",
        placeholder=None,
        extra_attrs=None
):
    """
    Render a field block with label, input, and error display.
        - label: optional override
        - required: optional override (otherwise use field.field_required)
        - help-text (auto or override)
        - error display
        - validation state classes
        - basic aria attributes
    """

    if not isinstance(field, BoundField):
        log_event(
            logger,
            logging.WARNING,
            "common.form_field.invalid_field",
            field_type=type(field).__name__,
        )
        return {
            'field': None,
            'rendered_field': '',
            'label': label or '',
            'required': False,
            'help': help or '',
            'wrapper_classes': wrapper_classes,
            'group_classes': group_classes,
            'subdivision': 'error',
            'has_errors': True,
            'field_id': '',
            'help_id': '',
            'error_id': '',
            'debug_error': f'form_field expected BoundField, got {type(field).__name__}: {repr(field)}',
        }

    # Defaukt: use Django's label
    label_text = label or field.label

    # Default: use the form field's required attribute
    required_flag = required if required is not None else field.field.required

    # Default: Django field help_text
    field_help_text = field.field.help_text or ''
    help_text = field_help_text if help is None else (help or '')

    state = _field_state(field)
    has_errors = bool(field.errors)

    field_id = field.id_for_label
    help_id = f"{field.auto_id}-help" if help_text else ""
    error_id = f"{field.auto_id}-errors" if has_errors else ""

    described_by_ids = " ".join(x for x in [help_id, error_id] if x) or None

    widget_attrs = {}

    if has_errors:
        widget_attrs['aria-invalid'] = 'true'
    if described_by_ids:
        widget_attrs['aria-describedby'] = described_by_ids
    if placeholder is not None:
        widget_attrs['placeholder'] = str(placeholder)

    if isinstance(extra_attrs, dict):
        widget_attrs.update(extra_attrs)

    rendered_field = field.as_widget(attrs=widget_attrs)

    return {
        'field': field,
        'rendered_field': rendered_field,
        'label': label_text,
        'required ': required_flag,
        'help': help_text,
        'wrapper_classes': wrapper_classes,
        'group_classes': group_classes,
        'state': state,
        'has_errors': has_errors,
        'field_id': field_id,
        'help_id': help_id,
        'error_id': error_id,
        'debug_error': ''
    }

    field_id = field.id_for_label
    help_id = f'{field.auto_id}-help' if help_text else ''
    error_id = f'{field.auto_id}-errors' if has_errors else ''

    described_by_ids = " ".join(
        x for x in [help_id, error_id] if x
    ) or None

    widget_attrs = {}
    if has_errors:
        widget_attrs['aria-invalid'] = 'true'
    if described_by_ids:
        widget_attrs['aria-describedby'] = described_by_ids
    if placeholder is not None:
        if isinstance(placeholder, str):
            widget_attrs['placeholder'] = placeholder
        elif isinstance(placeholder, (int, float)):
            widget_attrs['placeholder'] = str(placeholder)
        else:
            pass

    rendered_field = field.as_widget(attrs=widget_attrs)

    return {
        'field': field,
        'rendered_field': rendered_field,
        'label': label_text,
        'required': required_flag,
        'help': help_text,
        'wrapper_classes': wrapper_classes,
        'group_classes': group_classes,
        'subdivision': state,
        'has_errors': has_errors,
        'field_id': field_id,
        'help_id': help_id,
        'error_id': error_id,
        'debug_error': '',
    }
