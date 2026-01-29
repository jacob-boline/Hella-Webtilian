# hr_core/tests.py


from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase

from hr_common.utils.unified_logging import (get_request_id, REQUEST_ID_HEADER)
from hr_core.middleware import RequestIdMiddleware


class RequestIdMiddlewareTests(SimpleTestCase):
    def test_request_id_is_propagated_and_cleared(self):
        factory = RequestFactory()
        request = factory.get("/", HTTP_X_REQUEST_ID="req-123")
        captured = {}

        def get_response(_request):
            captured["request_id"] = get_request_id()
            return HttpResponse("ok")

        middleware = RequestIdMiddleware(get_response)
        resp = middleware(request)

        self.assertEqual(captured["request_id"], "req-123")
        self.assertEqual(resp[REQUEST_ID_HEADER], "req-123")
        self.assertIsNone(get_request_id())
