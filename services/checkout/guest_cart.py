"""Guest carts.

Shoppers who are not signed in never get a database row — their basket travels
in a signed cookie. Signing in hands the contents over to a persisted cart.
"""

import base64
import hashlib
import hmac
import json

import settings

COOKIE_NAME = "guest_cart"


def _sign(payload: bytes) -> str:
    return hmac.new(
        settings.SESSION_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()[:32]


def encode(items: list[dict]) -> str:
    payload = json.dumps(items, separators=(",", ":")).encode()
    body = base64.urlsafe_b64encode(payload).decode()
    return f"{body}.{_sign(payload)}"


def decode(cookie: str | None) -> list[dict]:
    """Read a cart cookie, discarding anything that fails its signature."""
    if not cookie or "." not in cookie:
        return []
    body, _, signature = cookie.rpartition(".")
    try:
        payload = base64.urlsafe_b64decode(body.encode())
    except (ValueError, TypeError):
        return []
    if not hmac.compare_digest(_sign(payload), signature):
        return []
    try:
        items = json.loads(payload.decode())
    except (UnicodeDecodeError, json.JSONDecodeError):
        return []
    return items if isinstance(items, list) else []


def add(items: list[dict], edition_id: int, quantity: int, unit_price_cents: int) -> list[dict]:
    for item in items:
        if item.get("edition_id") == edition_id:
            item["quantity"] = item.get("quantity", 0) + quantity
            return items
    items.append({
        "edition_id": edition_id,
        "quantity": quantity,
        "unit_price_cents": unit_price_cents,
    })
    return items


def remove(items: list[dict], edition_id: int) -> list[dict]:
    return [item for item in items if item.get("edition_id") != edition_id]
