# hr_common/utils/http/htmx.py

"""
HTML returned?
  NO  -> hx_trigger
  YES ->
    Modal via URL?        -> hx_load_modal
    Modal HTML returned?  ->
        Needs DOM ready?  -> merge_hx_trigger_after_settle
        Otherwise         -> merge_hx_trigger
    Not a modal?          ->
        Events needed?    -> merge_hx_trigger
        Otherwise         -> render only

Behavior Notes
    • empty swaps are blocked in htmx:beforeSwap -> 204 responses never swap HTML
    • modal flows are event-driven using hx_load_modal, never redirects
    • use afterSettle to display messsages in an incoming modal
    • merge_* helpers extend existing triggers; last write wins
    • If something fires too early, you chose the wrong helper
    • showMessage fires on htmx:afterSettle
"""

import json
from typing import Any

from django.http import HttpResponse


def merge_hx_trigger(resp: HttpResponse, extra: dict) -> HttpResponse:
    existing_raw = resp.get("HX-Trigger")
    existing: dict[str, Any] = {}

    if existing_raw:
        try:
            existing = json.loads(existing_raw)
            if not isinstance(existing, dict):
                existing = {}
        except (TypeError, ValueError):
            existing = {}

    existing.update(extra)
    resp["HX-Trigger"] = json.dumps(existing)
    return resp


def merge_hx_trigger_after_settle(resp: HttpResponse, extra: dict) -> HttpResponse:
    """
    Merge into HX-Trigger-After-Settle so events fire after transition swaps settle.
    Great for modal-content swaps where you want messages after new content is visible.
    """
    existing_raw = resp.get("HX-Trigger-After-Settle")
    existing: dict[str, Any] = {}

    if existing_raw:
        try:
            existing = json.loads(existing_raw)
            if not isinstance(existing, dict):
                existing = {}
        except (TypeError, ValueError):
            existing = {}

    existing.update(extra)
    resp["HX-Trigger-After-Settle"] = json.dumps(existing)
    return resp


def hx_trigger(payload: dict, *, status: int = 204) -> HttpResponse:
    resp = HttpResponse(status=status)
    resp["HX-Trigger"] = json.dumps(payload)
    return resp


def hx_load_modal(url: str, *, after_settle: dict[str, Any] | None = None, status: int = 204) -> HttpResponse:
    """
    Trigger the client to load/swap modal content via `loadModal` listener.
    `after_settle` events will be fired after #modal-content settles (via JS stash+afterSettle hook).
    """
    return hx_trigger({"loadModal": {"url": url, "afterSwapTriggers": after_settle or {}}}, status=status)


def is_htmx(request):
    """True if request was initiated by HTMX (HX-Request: true)."""
    return request.headers.get("HX-Request") == "true"
