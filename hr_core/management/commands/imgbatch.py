# hr_core/management/commands/imgbatch.py

import time
import uuid
from random import randint

import django_rq
from django.core.management.base import BaseCommand
from django.utils import timezone

from hr_core.image_batch import LAST_UPLOAD_KEY, scale_imgbatch
from hr_core.media_jobs import generate_variants_for_file
from hr_core.models import PendingVariant

LOCK_KEY = "img:batch_lock"
LOCK_TTL_SECONDS = 900
DEBOUNCE_SECONDS = 300


class Command(BaseCommand):
    help = "Process debounced image variant batches."

    def handle(self, *args, **options):
        connection = django_rq.get_connection("default")
        lock_value = str(uuid.uuid4())
        lock_acquired = connection.set(LOCK_KEY, lock_value, nx=True, ex=LOCK_TTL_SECONDS)

        if not lock_acquired:
            self.stdout.write(self.style.WARNING("Batch lock already held; exiting."))
            return

        try:
            while True:
                if not _wait_for_quiet_period(connection):
                    break

                processed_any = _process_pending()

                last_upload_ts = _get_last_upload_ts(connection)
                if last_upload_ts and _seconds_since(last_upload_ts) < DEBOUNCE_SECONDS:
                    continue

                if PendingVariant.objects.filter(processed_at__isnull=True).exists():
                    if processed_any:
                        continue
                    time.sleep(5)
                    continue

                break
        finally:
            scale_imgbatch(0)
            _release_lock(connection, lock_value)


def _get_last_upload_ts(connection) -> float | None:
    value = connection.get(LAST_UPLOAD_KEY)
    if not value:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _seconds_since(timestamp: float) -> float:
    return time.time() - timestamp


def _wait_for_quiet_period(connection) -> bool:
    while True:
        last_upload_ts = _get_last_upload_ts(connection)
        if last_upload_ts is None:
            return True
        if _seconds_since(last_upload_ts) >= DEBOUNCE_SECONDS:
            return True
        time.sleep(randint(10, 20))


def _process_pending() -> bool:
    pending = PendingVariant.objects.filter(processed_at__isnull=True).order_by("created_at")
    if not pending.exists():
        return False

    for row in pending:
        try:
            result = generate_variants_for_file(row.recipe_key, row.src_name)
        except Exception as exc:
            row.attempts += 1
            row.last_error = str(exc)
            row.save(update_fields=["attempts", "last_error"])
            continue

        if result.get("ok"):
            row.processed_at = timezone.now()
            row.last_error = ""
            row.save(update_fields=["processed_at", "last_error"])
        else:
            row.attempts += 1
            row.last_error = result.get("reason", "unknown_error")
            row.save(update_fields=["attempts", "last_error"])

    return True


def _release_lock(connection, lock_value: str) -> None:
    current = connection.get(LOCK_KEY)
    if current and current.decode("utf-8") == lock_value:
        connection.delete(LOCK_KEY)
