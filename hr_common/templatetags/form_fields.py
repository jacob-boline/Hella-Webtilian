# hr_common/templatetags/form_fields.py


from django import template

register = template.Library()


@register.inclusion_tag('hr_common/_form_field.html')
def form_field(
        field,
        label=None,
        required=None,
        help=None,
        wrapper_classes="field-row field-row-full",
        group_classes="field-group"
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
    # Defaukt: use Django's label
    label_text = label or field.label

    # Default: use the form field's required attribute
    required_flag = required if required is not None else field.field.required

    # Default: Django field help_text
    help_text = help or getattr(field, 'help_text', '')

    # Validation state
    form_is_bound = getattr(field.form, 'is_bound', False)
    has_errors = bool(field.errors)

    if has_errors:
        state = 'error'
    elif form_is_bound:
        state = 'valid'
    else:
        state = ''

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

    rendered_field = field.as_widget(attrs=widget_attrs)

    return {
        'field': field,
        'rendered_field': rendered_field,
        'label': label_text,
        'required': required_flag,
        'help': help_text,
        'wrapper_classes': wrapper_classes,
        'group_classes': group_classes,
        'state': state,
        'has_errors': has_errors,
        'field_id': field_id,
        'help_id': help_id,
        'error_id': error_id
    }
