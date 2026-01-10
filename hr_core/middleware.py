from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from structlog.contextvars import clear_contextvars

from hr_core.utils.unified_logging_core import (
    REQUEST_ID_HEADER,
    REQUEST_ID_META_KEY,
    generate_request_id,
    reset_request_id,
    set_request_id,
)


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
