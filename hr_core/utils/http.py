from functools import wraps
import json

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import redirect


def hx_login_required(view):
    @wraps(view)
    def _wrapped(request, *args, **kwargs):
        if request.user.is_authenticated:
            return view(request, *args, **kwargs)

        if is_htmx(request):
            # Explicitely handled here, but *could* just emit the 401 and let the global 401 handler take over
            resp = HttpResponse(status=401)
            resp["HX-Trigger"] = json.dumps({
                "authRequired": {
                    "message": "Please sign in.",
                    "focus": "#id_username",
                    "open_drawer": True,
                    "close_modal": True
                }
            })
            return resp

        # Non-HTMX: basically a placeholder until progressive enhancements join the party
        return redirect("index")
    return _wrapped


def hx_superuser_required(view):
    @wraps(view)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if is_htmx(request):
                resp = HttpResponse(status=401)
                resp["HX-Trigger"] = json.dumps({
                    "authRequired": {
                        "message": "Please sign in.",
                        "open_drawer": True,
                        "focus": "#id_username",
                        "close_modal": True
                    }
                })
                return resp
            return redirect("index")

        if not request.user.is_superuser:
            if is_htmx(request):
                resp = HttpResponse(status=403)
                resp["HX-Trigger"] = json.dumps({
                    "showMessage": "Not authorized."
                })
                return resp

            # Non-HTMX: prefer raising PermissionDenied
            # When later implementing progressive enhancements this can probably be handled more cleanly
            raise PermissionDenied("Superuser privileges required.")

        return view(request, *args, **kwargs)
    return _wrapped


def likely_session_expired(request) -> bool:
    if request.user.is_authenticated:
        return False
    # Check if the request has a session cookie
    return bool(request.COOKIES.get(settings.SESSION_COOKIE_NAME))


def is_htmx(request):
    return request.headers.get("HX-Request") == "true"


# DO NOT REMOVE reason="", CSRF_FAILURE_VIEW will call this with it as an argument and will TypeError if not present
def csrf_failure(request, _reason="", **_kwargs):
    if not is_htmx(request):
        return HttpResponse("Forbidden (CSRF verification failed).", status=403)

    if likely_session_expired(request):
        msg = "Your session expired. Please sign in again."
        resp = HttpResponse(status=403)
        resp["HX-Trigger"] = json.dumps({
            "showMessage": msg,
            "authRequired": {
                "message": msg,
                "open_drawer": True,
                "focus": "#id_username",
                "close_modal": True,
            }
        })
        return resp

    resp = HttpResponse(status=403)
    resp["HX-Trigger"] = json.dumps({
        "showMessage": "Security check failed. Please refresh and try again."
    })
    return resp
