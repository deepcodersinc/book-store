"""Payments and refunds.

Charges go out to Stripe; confirmations come back in over the public webhook.
Refunds branch on what was bought — a digital item settles immediately, a
physical one has to come back first.
"""

from data import orders as order_repo
from data import payments as payment_repo
from integrations import stripe_client
from packages.schemas.models import EditionFormat, PaymentStatus
from services.notifications import service as notifications


class PaymentError(RuntimeError):
    pass


def charge(order_id: int, amount_cents: int, order_number: str) -> dict:
    """Take payment for an order and record the provider reference."""
    payment_id = payment_repo.create_payment(order_id, amount_cents)
    result = stripe_client.create_charge(
        amount_cents=amount_cents,
        currency="USD",
        description=f"Bookstore order {order_number}",
        idempotency_key=order_number,
    )
    payment_repo.set_status(payment_id, PaymentStatus.PENDING.value, result["id"])
    return {"payment_id": payment_id, "provider_ref": result["id"], "status": result["status"]}


def handle_webhook(payload: bytes, signature: str) -> dict:
    """Process a payment confirmation posted by Stripe to the public endpoint."""
    if not stripe_client.verify_signature(payload, signature):
        raise PaymentError("Invalid webhook signature")

    event = stripe_client.parse_event(payload)
    if event.get("type") != "charge.succeeded":
        return {"handled": False, "reason": f"ignored event {event.get('type')}"}

    charge_ref = event["data"]["object"]["id"]
    payment = payment_repo.get_by_provider_ref(charge_ref)
    if not payment:
        return {"handled": False, "reason": "unknown charge"}

    payment_repo.set_status(payment["id"], PaymentStatus.SUCCEEDED.value)

    from services.orders import service as orders
    orders.mark_paid(payment["order_id"])
    return {"handled": True, "order_id": payment["order_id"]}


def confirm_locally(order_number: str) -> dict:
    """Mock-mode shortcut: replay the webhook Stripe would have sent."""
    order = order_repo.get_by_number(order_number)
    if not order:
        raise PaymentError(f"No such order: {order_number}")
    payment = payment_repo.payment_for_order(order["id"])
    if not payment or not payment["provider_ref"]:
        raise PaymentError("Order has no payment to confirm")

    import json
    event = stripe_client.build_webhook_event(payment["provider_ref"], order_number)
    return handle_webhook(json.dumps(event).encode(), signature="")


def refund_item(order_item_id: int, reason: str = "") -> dict:
    """Refund a single line. Physical goods must be returned before it settles."""
    item = order_repo.get_order_item(order_item_id)
    if not item:
        raise PaymentError("No such order item")

    payment = payment_repo.payment_for_order(item["order_id"])
    if not payment or payment["status"] != PaymentStatus.SUCCEEDED.value:
        raise PaymentError("Order has no settled payment")

    is_digital = EditionFormat(item["format"]).is_digital
    amount = item["unit_price_cents"] * item["quantity"]

    if is_digital:
        stripe_client.create_refund(payment["provider_ref"], amount)
        status = "settled"
    else:
        status = "awaiting_return"

    refund_id = payment_repo.create_refund(
        payment_id=payment["id"],
        order_item_id=order_item_id,
        amount_cents=amount,
        reason=reason,
        requires_return=not is_digital,
        status=status,
    )
    notifications.refund_opened(item, amount, requires_return=not is_digital)
    return {"refund_id": refund_id, "status": status, "amount_cents": amount}


def list_refunds() -> list[dict]:
    return payment_repo.list_refunds()
