"""Orders and their lines. Owned by the order service."""

from data import db


def create_order(order_number: str, customer_id: int | None, email: str,
                 subtotal_cents: int, discount_cents: int, tax_cents: int,
                 total_cents: int, country_code: str, pricing_scheme: str,
                 checkout_version: str) -> int:
    return db.execute(
        """
        INSERT INTO orders (
            order_number, customer_id, email, subtotal_cents, discount_cents,
            tax_cents, total_cents, country_code, pricing_scheme, checkout_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (order_number, customer_id, email, subtotal_cents, discount_cents,
         tax_cents, total_cents, country_code, pricing_scheme, checkout_version),
    )


def add_order_item(order_id: int, edition_id: int, quantity: int,
                   unit_price_cents: int, fmt: str) -> int:
    return db.execute(
        """
        INSERT INTO order_items (order_id, edition_id, quantity, unit_price_cents, format)
        VALUES (?, ?, ?, ?, ?)
        """,
        (order_id, edition_id, quantity, unit_price_cents, fmt),
    )


def get_order(order_id: int) -> dict | None:
    return db.query_one("SELECT * FROM orders WHERE id = ?", (order_id,))


def get_by_number(order_number: str) -> dict | None:
    return db.query_one("SELECT * FROM orders WHERE order_number = ?", (order_number,))


def items_for_order(order_id: int) -> list[dict]:
    return db.query(
        """
        SELECT oi.*, b.title, b.author, b.slug, e.asset_path
        FROM order_items oi
        JOIN editions e ON e.id = oi.edition_id
        JOIN books b ON b.id = e.book_id
        WHERE oi.order_id = ?
        ORDER BY oi.id
        """,
        (order_id,),
    )


def get_order_item(order_item_id: int) -> dict | None:
    return db.query_one(
        """
        SELECT oi.*, o.email, o.customer_id, b.title, e.asset_path
        FROM order_items oi
        JOIN orders o ON o.id = oi.order_id
        JOIN editions e ON e.id = oi.edition_id
        JOIN books b ON b.id = e.book_id
        WHERE oi.id = ?
        """,
        (order_item_id,),
    )


def list_orders(customer_id: int | None = None, limit: int = 50) -> list[dict]:
    if customer_id is not None:
        return db.query(
            "SELECT * FROM orders WHERE customer_id = ? ORDER BY created_at DESC LIMIT ?",
            (customer_id, limit),
        )
    return db.query("SELECT * FROM orders ORDER BY created_at DESC LIMIT ?", (limit,))


def set_status(order_id: int, status: str) -> None:
    db.execute(
        "UPDATE orders SET status = ?, updated_at = datetime('now') WHERE id = ?",
        (status, order_id),
    )


def set_item_fulfillment(order_item_id: int, status: str) -> None:
    db.execute(
        "UPDATE order_items SET fulfillment_status = ? WHERE id = ?",
        (status, order_item_id),
    )


def next_order_number() -> str:
    row = db.query_one("SELECT COUNT(*) AS n FROM orders")
    return f"ORD-{1000 + (row['n'] if row else 0) + 1}"
