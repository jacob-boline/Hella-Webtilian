# hr_core/middleware/request_id.py
from django.http import HttpRequest, HttpResponse
from structlog.contextvars import clear_contextvars

from hr_common.utils.unified_logging import generate_request_id, REQUEST_ID_HEADER, REQUEST_ID_META_KEY, reset_request_id, set_request_id


# 1) RequestIdMiddleware
#    - Ensures every request has a stable request_id
#    - Stores request_id in a contextvar and binds it to structlog contextvars
#    - Adds X-Request-ID header to every response

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
