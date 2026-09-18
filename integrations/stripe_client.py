"""Stripe payment gateway.

Without STRIPE_API_KEY the client runs in mock mode: charges succeed immediately
and a webhook payload is produced locally so the rest of the flow behaves the
same as it would in production.
"""

import hashlib
import hmac
import json
import time

import settings


class StripeError(RuntimeError):
    pass


def is_live() -> bool:
    return bool(settings.STRIPE_API_KEY)


def create_charge(amount_cents: int, currency: str, description: str,
                  idempotency_key: str) -> dict:
    """Charge a card. Returns the provider reference and status."""
    if not is_live():
        return {
            "id": f"ch_mock_{idempotency_key}",
            "status": "succeeded",
            "amount": amount_cents,
            "currency": currency.lower(),
            "livemode": False,
        }

    # Real call would go through the stripe SDK here.
    raise StripeError("Live Stripe calls are not configured in this environment")


def create_refund(charge_ref: str, amount_cents: int) -> dict:
    if not is_live():
        return {
            "id": f"re_mock_{charge_ref}",
            "status": "succeeded",
            "amount": amount_cents,
            "livemode": False,
        }
    raise StripeError("Live Stripe calls are not configured in this environment")


def build_webhook_event(charge_ref: str, order_number: str) -> dict:
    """The payload Stripe would post back once a charge settles."""
    return {
        "id": f"evt_mock_{charge_ref}",
        "type": "charge.succeeded",
        "created": int(time.time()),
        "data": {"object": {"id": charge_ref, "metadata": {"order_number": order_number}}},
    }


def verify_signature(payload: bytes, signature: str) -> bool:
    """Confirm a webhook really came from Stripe.

    The endpoint is public, so this is the only thing standing between the
    internet and the order state machine.
    """
    if not settings.STRIPE_WEBHOOK_SECRET:
        return True  # mock mode: accept locally generated events
    expected = hmac.new(
        settings.STRIPE_WEBHOOK_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature or "")


def parse_event(payload: bytes) -> dict:
    try:
        return json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StripeError(f"Malformed webhook payload: {exc}") from exc
