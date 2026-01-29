# hr_core/middleware.py


"""
Project middleware.

Contains:
1) RequestIdMiddleware
   - Ensures every request has a stable request_id
   - Stores request_id in a contextvar and binds it to structlog contextvars
   - Adds X-Request-ID header to every response

2) HtmxExceptionMiddleware
   - Converts common exceptions (404, PermissionDenied) into HTMX-friendly
     responses when HX-Request is true.
   - For HTMX:
       * returns appropriate status code
       * emits HX-Trigger events (showMessage, closeModal)
   - For non-HTMX:
       * re-raises to let Django's normal error views handle it
"""

from __future__ import annotations

import json
from collections.abc import Callable

from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse
from structlog.contextvars import clear_contextvars

from hr_common.utils.htmx_responses import likely_session_expired
from hr_common.utils.unified_logging import (generate_request_id, REQUEST_ID_HEADER, REQUEST_ID_META_KEY, reset_request_id, set_request_id)
from utils.http.htmx import is_htmx


class RequestIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = request.META.get(REQUEST_ID_META_KEY) or generate_request_id()
        token = set_request_id(request_id)
        request.request_id = request_id
        try:
            resp = self.get_response(request)
        finally:
            clear_contextvars()
            reset_request_id(token)
        resp[REQUEST_ID_HEADER] = request_id
        return resp


class HtmxExceptionMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        try:
            return self.get_response(request)
        except Http404:
            if is_htmx(request):
                resp = HttpResponse(status=404)
                resp["HX-Trigger"] = json.dumps({"showMessage": "Not found.", "closeModal": None})
                return resp
            raise

        except PermissionDenied:
            if is_htmx(request):
                msg = "Not authorized."
                if likely_session_expired(request):
                    msg = "Your session may have expired. Please sign in again."

                resp = HttpResponse(status=403)
                resp["HX-Trigger"] = json.dumps({"showMessage": msg, "closeModal": None})
                return resp
            raise
