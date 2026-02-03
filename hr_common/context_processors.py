# hr_common/context_processors.py

from django.conf import settings


def template_flags(request):
    return {
        "debug": bool(settings.DEBUG)
    }
