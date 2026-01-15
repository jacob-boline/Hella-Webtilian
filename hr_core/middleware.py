from __future__ import annotations

import json

from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse, Http404
from structlog.contextvars import clear_contextvars

from hr_core.utils.unified_logging_core import (
    REQUEST_ID_HEADER,
    REQUEST_ID_META_KEY,
    generate_request_id,
    reset_request_id,
    set_request_id,
)
from hr_core.utils.http import is_htmx, likely_session_expired


class RequestIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = request.META.get(REQUEST_ID_META_KEY) or generate_request_id()
        token = set_request_id(request_id)
        request.request_id = request_id
        try:
            response = self.get_response(request)
        finally:
            clear_contextvars()
            reset_request_id(token)
        response[REQUEST_ID_HEADER] = request_id
        return response


class HtmxExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Http404:
            if is_htmx(request):
                resp = HttpResponse(status=404)
                resp['HX-Trigger'] = json.dumps({
                    'showMessage': 'Not found.',
                    'closeModal': None
                })
                return resp
            raise

        except PermissionDenied:
            if is_htmx(request):
                msg = 'Not authorized.'
                if likely_session_expired(request):
                    msg = 'Your session may have expired. Please sign in again.'

                resp = HttpResponse(status=403)
                resp['HX-Trigger'] = json.dumps({
                    'showMessage': msg,
                    'closeModal': None
                })
                return resp
            raise
