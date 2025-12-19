# hr_core/mixins.py


class HtmxTemplateMixin:
    """
    Lets a CBV choose between a full-page template and an HTMX/modal partial.

    Use:
        - template_name      -> full page (extends base.html)
        - htmx_template_name -> modal/partial
    """

    htmx_template_name = None

    def get_template_names(self):
        if self.htmx_template_name:
            return [self.htmx_template_name]

        return super().get_template_names()
