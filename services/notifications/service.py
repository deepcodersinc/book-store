"""Customer-facing messages.

Every message is recorded whether or not it actually leaves the building, so the
admin console can show an outbox and nothing is invisible in a demo.
"""

from data import notifications as notification_repo
from integrations import email_client, sms_client
from services.identity import service as identity


def _send(type_: str, recipient: str, subject: str, body: str) -> int:
    result = email_client.send(recipient, subject, body)
    status = "sent" if result.get("accepted") else "failed"
    return notification_repo.record(type_, recipient, subject, body, status=status)


def _send_text(type_: str, recipient: str, subject: str, body: str) -> int:
    """Same contract as _send, over SMS. Recorded in the outbox either way."""
    result = sms_client.send(recipient, body)
    status = "sent" if result.get("accepted") else "failed"
    return notification_repo.record(type_, recipient, subject, body,
                                    channel="sms", status=status)


def order_confirmed(order: dict, items: list[dict]) -> int:
    lines = "\n".join(
        f"  - {item['title']} ({item['format']}) x{item['quantity']}" for item in items
    )
    body = (
        f"Thanks for your order, {order['order_number']}.\n\n"
        f"{lines}\n\n"
        f"Total: ${order['total_cents'] / 100:.2f}"
    )
    return _send("order_confirmed", order["email"],
                 f"Order {order['order_number']} confirmed", body)


def shipment_dispatched(order: dict, tracking_number: str) -> int:
    subject = f"Order {order['order_number']} has shipped"
    body = (
        f"Your order {order['order_number']} is on its way.\n\n"
        f"Tracking number: {tracking_number}"
    )
    notification_id = _send("shipment_dispatched", order["email"], subject, body)

    # A text as well, for accounts that gave us a number. Guest orders, and
    # accounts without one, simply get the email.
    mobile = identity.mobile_for_customer(order.get("customer_id"))
    if mobile:
        _send_text("shipment_dispatched", mobile, subject,
                   f"LocalBooks: order {order['order_number']} has shipped. "
                   f"Tracking {tracking_number}.")
    return notification_id


def download_ready(order: dict, title: str, token: str) -> int:
    body = (
        f"Your copy of {title} is ready.\n\n"
        f"Download: /download/{token}\n"
        f"The link expires in 72 hours."
    )
    return _send("download_ready", order["email"], f"{title} is ready to download", body)


def refund_opened(item: dict, amount_cents: int, requires_return: bool) -> int:
    if requires_return:
        body = (
            f"We have started a refund of ${amount_cents / 100:.2f} for {item['title']}.\n\n"
            f"Please send the book back — the refund settles once it arrives."
        )
    else:
        body = (
            f"We have refunded ${amount_cents / 100:.2f} for {item['title']}.\n\n"
            f"The amount should appear on your statement shortly."
        )
    return _send("refund_opened", item["email"], f"Refund for {item['title']}", body)


def low_stock_alert(titles: list[str]) -> int:
    body = "These titles are at or below their reorder threshold:\n\n" + "\n".join(
        f"  - {title}" for title in titles
    )
    return _send("low_stock", "ops@bookstore.example", "Low stock report", body)


def outbox(limit: int = 50) -> list[dict]:
    return notification_repo.list_recent(limit)
