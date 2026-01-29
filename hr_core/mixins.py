# hr_core/mixins.py


from __future__ import annotations

from django.views.generic.base import TemplateResponseMixin


class HtmxTemplateMixin(TemplateResponseMixin):
    """
    Progressive enhancement helper.

    When used with a TemplateResponseMixin-based CBV (TemplateView/DetailView/etc.),
    allows swapping the template to an HTMX-specific partial.
    """

    htmx_template_name: str | None = None

    def get_template_names(self):
        if self.htmx_template_name:
            return [self.htmx_template_name]

        return super().get_template_names()
