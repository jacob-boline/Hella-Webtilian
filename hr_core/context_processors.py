from django.conf import settings


def vite_flags(request):
    return {
        "USING_TUNNEL": getattr(settings, "USING_TUNNEL", False),
        "DEBUG": settings.DEBUG,
    }
