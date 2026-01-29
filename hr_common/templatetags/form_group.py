# hr_common/templatetags/form_group.py

from django import template

register = template.Library()

_UNSET = object()


def _coerce_placeholder(value):
    if value is None:
        return None
    if isinstance(value, (str, int, float)):
        return str(value)
    return None


def _field_state(bound_field):
    form_is_bound = getattr(bound_field.form, "is_bound", False)
    has_errors = bool(bound_field.errors)

    if has_errors:
        return "error"
    if form_is_bound:
        return "valid"
    return "neutral"


@register.inclusion_tag("hr_common/_form_group.html")
def form_group(field, label=_UNSET, required=None, help=None, group_classes="field-group", placeholder=None, extra_attrs=None):
    if label is _UNSET:
        label_text = field.label
    elif label is False or label == "":
        label_text = None
    else:
        label_text = label

    required_flag = required if required is not None else field.field.required

    # Default to Django's help_text if non is given
    help_text = help if help is not None else (field.field.help_text or "")

    state = _field_state(field)
    has_errors = bool(field.errors)

    field_id = field.id_for_label
    help_id = f"{field.auto_id}-help" if help_text else ""
    error_id = f"{field.auto_id}-errors" if has_errors else ""

    described_by_ids = " ".join(x for x in [help_id, error_id] if x) or None

    widget_attrs = {}
    if has_errors:
        widget_attrs["aria-invalid"] = "true"
    if described_by_ids:
        widget_attrs["aria-describedby"] = described_by_ids

    ph = _coerce_placeholder(placeholder)
    if ph is not None:
        widget_attrs["placeholder"] = ph

    if isinstance(extra_attrs, dict):
        widget_attrs.update(extra_attrs)

    rendered_field = field.as_widget(attrs=widget_attrs)

    return {
        "field": field,
        "rendered_field": rendered_field,
        "label": label_text,
        "required": required_flag,
        "help": help_text,
        "group_classes": group_classes,
        "state": state,
        "has_errors": has_errors,
        "field_id": field_id,
        "help_id": help_id,
        "error_id": error_id,
    }
