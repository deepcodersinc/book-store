"""Payment and refund records. Owned by the payment service."""

from data import db


def create_payment(order_id: int, amount_cents: int, provider_ref: str | None = None,
                   provider: str = "stripe") -> int:
    return db.execute(
        """
        INSERT INTO payments (order_id, provider, provider_ref, amount_cents)
        VALUES (?, ?, ?, ?)
        """,
        (order_id, provider, provider_ref, amount_cents),
    )


def get_payment(payment_id: int) -> dict | None:
    return db.query_one("SELECT * FROM payments WHERE id = ?", (payment_id,))


def get_by_provider_ref(provider_ref: str) -> dict | None:
    return db.query_one("SELECT * FROM payments WHERE provider_ref = ?", (provider_ref,))


def payment_for_order(order_id: int) -> dict | None:
    return db.query_one(
        "SELECT * FROM payments WHERE order_id = ? ORDER BY id DESC LIMIT 1",
        (order_id,),
    )


def set_status(payment_id: int, status: str, provider_ref: str | None = None) -> None:
    if provider_ref:
        db.execute(
            "UPDATE payments SET status = ?, provider_ref = ? WHERE id = ?",
            (status, provider_ref, payment_id),
        )
    else:
        db.execute("UPDATE payments SET status = ? WHERE id = ?", (status, payment_id))


def create_refund(payment_id: int, order_item_id: int | None, amount_cents: int,
                  reason: str, requires_return: bool, status: str) -> int:
    return db.execute(
        """
        INSERT INTO refunds (payment_id, order_item_id, amount_cents, reason,
                             requires_return, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (payment_id, order_item_id, amount_cents, reason, int(requires_return), status),
    )


def list_refunds() -> list[dict]:
    return db.query(
        """
        SELECT r.*, o.order_number
        FROM refunds r
        JOIN payments p ON p.id = r.payment_id
        JOIN orders o ON o.id = p.order_id
        ORDER BY r.created_at DESC
        """
    )
