# hr_core/mixins.py


from hr_core.utils import http

class HtmxTemplateMixin:
    """
    Lets a CBV choose between a full-page template and an HTMX/modal partial.

    Use:
        - template_name      -> full page (extends base.html)
        - htmx_template_name -> modal/partial
    """

    htmx_template_name = None

    def get_template_names(self):

        request = getattr(self, 'request', None)
        if request is not None and http.is_htmx(request) and self.htmx_template_name:
            return [self.htmx_template_name]

        return super().get_template_names()