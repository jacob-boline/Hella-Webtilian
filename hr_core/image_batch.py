# hr_core/image_batch.py

import json
import os
import time
import urllib.request

import django_rq

from hr_core.models import PendingVariant

ALLOWED_RECIPE_KEYS = {"variant", "post_hero", "about"}
LAST_UPLOAD_KEY = "img:last_upload_ts"
LAST_UPLOAD_TTL_SECONDS = 3600


def _enqueue_immediate(recipe_key: str, src_name: str) -> None:
    q = django_rq.get_queue("default")
    q.enqueue("hr_core.media_jobs.generate_variants_for_file", recipe_key, src_name)


def scale_imgbatch(quantity: int) -> bool:
    app_name = os.getenv("HEROKU_APP_NAME")
    api_token = os.getenv("HEROKU_API_TOKEN")
    if not app_name or not api_token:
        return False

    url = f"https://api.heroku.com/apps/{app_name}/formation/imgbatch"
    payload = json.dumps({"quantity": quantity}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        method="PATCH",
        headers={
            "Authorization": f"Bearer {api_token}",
            "Accept": "application/vnd.heroku+json; version=3",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return 200 <= response.status < 300
    except Exception:
        return False


def schedule_image_variants(recipe_key: str, src_name: str) -> None:
    if recipe_key not in ALLOWED_RECIPE_KEYS:
        return

    enable_batcher = os.getenv("ENABLE_DEBOUNCED_IMAGE_BATCHER", "").lower() == "true"

    if not enable_batcher:
        _enqueue_immediate(recipe_key, src_name)
        return

    PendingVariant.objects.get_or_create(recipe_key=recipe_key, src_name=src_name)

    connection = django_rq.get_connection("default")
    now_ts = time.time()
    connection.setex(LAST_UPLOAD_KEY, LAST_UPLOAD_TTL_SECONDS, str(now_ts))

    on_heroku = os.getenv("DYNO") is not None
    if not on_heroku or not os.getenv("HEROKU_APP_NAME") or not os.getenv("HEROKU_API_TOKEN"):
        _enqueue_immediate(recipe_key, src_name)
        return

    scale_imgbatch(1)
