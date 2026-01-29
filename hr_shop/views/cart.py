# hr_shop/views/cart.py

import logging
import time
from typing import Any

from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from hr_common.utils.http.htmx import hx_trigger, merge_hx_trigger_after_settle
from hr_common.utils.unified_logging import log_event
from hr_shop.cart import add_to_cart, Cart, CartItemNotFoundError, get_cart
from hr_shop.models import Product

logger = logging.getLogger(__name__)

# -----------------------------
# Idempotency (session-scoped)
# -----------------------------
# “Add” actions are naturally non-idempotent (repeat request => more items)
# unless we introduce an idempotency key.
#
# This implements a best-practice middle ground for SPA/HTMX:
# - client sends X-Idempotency-Key (UUID per click)
# - server stores the resulting HX trigger payload for a short TTL
# - repeats with the same key return the same trigger payload without re-adding
#
# Session scope is intentional: it avoids cross-user leakage and keeps infra simple.
_IDEMP_SESSION_KEY = "hr_shop_cart_idem"
_IDEMP_TTL_SECONDS = 120  # short window to catch double-clicks / retries


def _get_idempotency_key(request) -> str | None:
    """
    Return an idempotency key if provided by the client.

    Recommended client header: X-Idempotency-Key: <uuid>
    (Also accepts Idempotency-Key as a fallback.)
    """
    return request.headers.get("X-Idempotency-Key") or request.headers.get("Idempotency-Key") or None


def _idem_prune(store: dict[str, Any], now: int) -> None:
    """
    Prune expired entries in-place.
    Store shape:
        { "<key>": {"ts": <unix>, "payload": <dict>} }
    """
    expired = []
    for k, v in store.items():
        try:
            ts = int(v.get("ts", 0))
        except (TypeError, ValueError, AttributeError):
            ts = 0
        if not ts or (now - ts) > _IDEMP_TTL_SECONDS:
            expired.append(k)
    for k in expired:
        store.pop(k, None)


def _idem_get_payload(request, key: str) -> dict | None:
    store = request.session.get(_IDEMP_SESSION_KEY)
    if not isinstance(store, dict):
        store = {}
        request.session[_IDEMP_SESSION_KEY] = store

    now = int(time.time())
    _idem_prune(store, now)

    entry = store.get(key)
    if not isinstance(entry, dict):
        return None

    payload = entry.get("payload")
    if not isinstance(payload, dict):
        return None

    return payload


def _idem_store_payload(request, key: str, payload: dict) -> None:
    store = request.session.get(_IDEMP_SESSION_KEY)
    if not isinstance(store, dict):
        store = {}
        request.session[_IDEMP_SESSION_KEY] = store

    now = int(time.time())
    _idem_prune(store, now)

    store[key] = {"ts": now, "payload": payload}
    request.session[_IDEMP_SESSION_KEY] = store
    request.session.modified = True


# -----------------------------
# Parsing helpers
# -----------------------------
def _parse_qty_min1(request, default: int = 1) -> int:
    try:
        q = int(request.POST.get("quantity", default))
    except (TypeError, ValueError):
        q = default
    return max(q, 1)


def _parse_qty_allow0(request, default: int = 1) -> int:
    try:
        q = int(request.POST.get("quantity", default))
    except (TypeError, ValueError):
        q = default
    return max(q, 0)


def _parse_selected_option_value_ids(request) -> list[int]:
    """
    Parse selected product option value ids from POST payload:
      opt_<something> = <value_id>

    Ignores invalid values. Caller can treat empty result as an error.
    """
    selected_value_ids: list[int] = []
    for key, value in request.POST.items():
        if not key.startswith("opt_") or not value:
            continue
        try:
            selected_value_ids.append(int(value))
        except (TypeError, ValueError):
            # Malformed option ids are ignored; we fail later if none are valid.
            pass
    return selected_value_ids


# -----------------------------
# Trigger payload helpers
# -----------------------------
def _cart_item_count(cart: Cart) -> int:
    """
    Item count displayed in UI.

    IMPORTANT: Cart.__len__ returns total *units* (sum of quantities),
    not distinct line items. That’s usually what you want for a cart badge.
    """
    return len(cart)


def _cart_triggers(cart: Cart, *, message: str | None = None) -> dict[str, Any]:
    """
    Standard cart-related trigger payloads.
    Keeps event shape consistent across endpoints.
    """
    payload: dict[str, Any] = {"updateCart": {"item_count": _cart_item_count(cart)}}
    if message:
        payload["showMessage"] = {"message": message}
    return payload


# -----------------------------
# Response helpers
# -----------------------------
def _render_cart_modal(request, *, message: str | None = None) -> HttpResponse:
    """
    Render the cart partial intended for swapping into #modal-content, and attach
    triggers via HX-Trigger-After-Settle so UI updates/messages happen after
    transition swaps settle.
    """
    cart = get_cart(request)
    resp = render(request, "hr_shop/shop/_view_cart.html", {"cart": list(cart), "total": cart.total()})
    return merge_hx_trigger_after_settle(resp, _cart_triggers(cart, message=message))


def _hx_trigger_idempotent(request, payload: dict, *, status: int = 204) -> HttpResponse:
    """
    Return HX triggers, but if the request includes an idempotency key that has
    already been seen recently in this session, return the previously stored payload
    instead of re-executing the mutation.

    This is primarily meant for “add” endpoints to prevent double-click duplicates.
    """
    key = _get_idempotency_key(request)
    if not key:
        return hx_trigger(payload, status=status)

    prior = _idem_get_payload(request, key)
    if prior is not None:
        return hx_trigger(prior, status=status)

    _idem_store_payload(request, key, payload)
    return hx_trigger(payload, status=status)


# -----------------------------
# Views
# -----------------------------
@require_POST
def add_variant_to_cart(request, variant_slug):
    # If we’ve already processed this “add” click in the last TTL window, replay the
    # prior trigger payload and do not add again.
    idem_key = _get_idempotency_key(request)
    if idem_key:
        prior = _idem_get_payload(request, idem_key)
        if prior is not None:
            log_event(logger, logging.INFO, "cart.add_variant.idempotent_replay", variant_slug=variant_slug)
            return hx_trigger(prior, status=204)

    quantity = _parse_qty_min1(request)
    cart, variant, line_qty = add_to_cart(request, variant_slug, quantity)

    log_event(logger, logging.INFO, "cart.add_variant", variant_slug=variant_slug, quantity=quantity, line_qty=line_qty, cart_item_count=_cart_item_count(cart))

    payload = _cart_triggers(cart, message=f"Added {variant.product.name} x{line_qty} to cart")

    # Trigger-only: no HTML swap needed.
    # Stored payload enables best-effort idempotency for rapid replays.
    if idem_key:
        _idem_store_payload(request, idem_key, payload)
    return hx_trigger(payload, status=204)


@require_POST
def add_to_cart_by_options(request, product_slug):
    # Idempotency replay (see add_variant_to_cart for rationale).
    idem_key = _get_idempotency_key(request)
    if idem_key:
        prior = _idem_get_payload(request, idem_key)
        if prior is not None:
            log_event(logger, logging.INFO, "cart.add_by_options.idempotent_replay", product_slug=product_slug)
            return hx_trigger(prior, status=204)

    product = get_object_or_404(Product, slug=product_slug)

    selected_value_ids = _parse_selected_option_value_ids(request)
    if not selected_value_ids:
        log_event(logger, logging.WARNING, "cart.add_by_options.no_options", product_slug=product_slug)
        return HttpResponseBadRequest("No options selected")

    selected_set = set(selected_value_ids)
    variants = product.variants.filter(active=True).prefetch_related("option_values")

    chosen_variant = None
    for variant in variants:
        if variant.option_value_ids_set == selected_set:
            chosen_variant = variant
            break

    if not chosen_variant:
        log_event(logger, logging.WARNING, "cart.add_by_options.no_variant", product_slug=product_slug, selected_value_ids=selected_value_ids)
        return HttpResponseBadRequest("No variant for selected options")

    quantity = _parse_qty_min1(request)
    cart, variant, line_qty = add_to_cart(request, chosen_variant.slug, quantity)

    log_event(logger, logging.INFO, "cart.add_by_options",
        product_slug=product_slug,
        variant_slug=variant.slug,
        quantity=quantity,
        line_qty=line_qty,
        cart_item_count=_cart_item_count(cart)
    )

    payload = _cart_triggers(cart, message=f"Added {variant.product.name} x{line_qty} to cart")

    if idem_key:
        _idem_store_payload(request, idem_key, payload)
    return hx_trigger(payload, status=204)


def view_cart(request):
    return _render_cart_modal(request)


@require_POST
def set_cart_quantity(request, variant_id: int):
    cart = Cart(request)
    quantity = _parse_qty_allow0(request)

    try:
        cart.set_quantity(variant_id, quantity)
        log_event(logger, logging.INFO, "cart.quantity_set", variant_id=variant_id, quantity=quantity, cart_item_count=_cart_item_count(cart))
        return _render_cart_modal(request)

    except CartItemNotFoundError:
        # account for multiple tabs opened by user
        if quantity == 0:
            log_event(logger, logging.INFO, "cart.quantity_set.idempotent_missing_zero", variant_id=variant_id)
            return _render_cart_modal(request, message="Item was already removed.")

        # Likely an issue with the code trying to add an item by defining qty
        log_event(logger, logging.WARNING, "cart.quantity_set.missing_item", variant_id=variant_id, quantity=quantity)
        return HttpResponseBadRequest("Item must be present in the cart before it can be updated.")


@require_POST
def remove_from_cart(request, variant_id: int):
    cart = Cart(request)

    try:
        cart.remove(variant_id)
        msg = "Removed item from cart."
        log_event(logger, logging.INFO, "cart.item_removed", variant_id=variant_id, cart_item_count=_cart_item_count(cart))
    except CartItemNotFoundError:
        msg = "Item was already removed."
        log_event(logger, logging.INFO, "cart.item_missing", variant_id=variant_id, cart_item_count=_cart_item_count(cart))

    return _render_cart_modal(request, message=msg)
