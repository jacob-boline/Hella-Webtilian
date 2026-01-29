# hr_common/middleware/logging_context.py

from __future__ import annotations

from hr_common.utils.unified_logging import reset_user_id, set_user_id


class RequestUserContextMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        uid = user.id if getattr(user, 'is_authenticated', False) else None

        tok = set_user_id(uid)
        try:
            return self.get_response(request)
        finally:
            reset_user_id(tok)
