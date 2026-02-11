# hr_core/tests.py

import tempfile
from pathlib import Path
from io import StringIO
from unittest.mock import Mock
from unittest.mock import patch

from django.core.management import call_command
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase
from django.test import override_settings

from hr_common.utils.unified_logging import (get_request_id, REQUEST_ID_HEADER)
from hr_core.middleware import RequestIdMiddleware
from hr_core.media_jobs import CropSpec
from hr_core.media_jobs import Recipe


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


class MediaSweepCommandTests(SimpleTestCase):
    def test_run_now_processes_sources_inline(self):
        with tempfile.TemporaryDirectory() as media_root:
            src_dir = Path(media_root) / "variants"
            src_dir.mkdir(parents=True)
            (src_dir / "shirt.png").write_bytes(b"fake")

            recipe = Recipe(
                src_root="media",
                src_rel_dir="variants",
                out_subdir="opt_webp",
                widths=(256,),
                crop=CropSpec(1, 1),
            )

            with override_settings(MEDIA_ROOT=media_root):
                with patch("hr_core.management.commands.media_sweep.RECIPES", {"variant": recipe}):
                    with patch("hr_core.management.commands.media_sweep.generate_variants_for_file") as gen:
                        call_command("media_sweep", "--recipe", "variant", "--run-now")

            gen.assert_called_once_with("variant", "variants/shirt.png")

    def test_enqueue_mode_prints_worker_hint(self):
        with tempfile.TemporaryDirectory() as media_root:
            src_dir = Path(media_root) / "variants"
            src_dir.mkdir(parents=True)
            (src_dir / "shirt.png").write_bytes(b"fake")

            recipe = Recipe(
                src_root="media",
                src_rel_dir="variants",
                out_subdir="opt_webp",
                widths=(256,),
                crop=CropSpec(1, 1),
            )

            queue = Mock()
            out = StringIO()
            with override_settings(MEDIA_ROOT=media_root):
                with patch("hr_core.management.commands.media_sweep.RECIPES", {"variant": recipe}):
                    with patch("hr_core.management.commands.media_sweep.django_rq.get_queue", return_value=queue):
                        call_command("media_sweep", "--recipe", "variant", stdout=out)

            queue.enqueue.assert_called_once_with("hr_core.media_jobs.generate_variants_for_file", "variant", "variants/shirt.png")
            self.assertIn("python manage.py rqworker default", out.getvalue())

    def test_enqueue_falls_back_to_inline_when_rq_unavailable(self):
        with tempfile.TemporaryDirectory() as media_root:
            src_dir = Path(media_root) / "variants"
            src_dir.mkdir(parents=True)
            (src_dir / "shirt.png").write_bytes(b"fake")

            recipe = Recipe(
                src_root="media",
                src_rel_dir="variants",
                out_subdir="opt_webp",
                widths=(256,),
                crop=CropSpec(1, 1),
            )

            out = StringIO()
            with override_settings(MEDIA_ROOT=media_root):
                with patch("hr_core.management.commands.media_sweep.RECIPES", {"variant": recipe}):
                    with patch("hr_core.management.commands.media_sweep.django_rq.get_queue", side_effect=RuntimeError("redis down")):
                        with patch("hr_core.management.commands.media_sweep.generate_variants_for_file") as gen:
                            call_command("media_sweep", "--recipe", "variant", stdout=out)

            gen.assert_called_once_with("variant", "variants/shirt.png")
            output = out.getvalue()
            self.assertIn("falling back to inline processing", output)
            self.assertIn("Processed 1 source files inline", output)
