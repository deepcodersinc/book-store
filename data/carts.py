"""Persisted carts. Only signed-in shoppers get one; guest carts stay in a cookie."""

from data import db


def get_active_cart(customer_id: int) -> dict | None:
    return db.query_one(
        "SELECT * FROM carts WHERE customer_id = ? AND status = 'active'",
        (customer_id,),
    )


def get_or_create_cart(customer_id: int) -> int:
    cart = get_active_cart(customer_id)
    if cart:
        return cart["id"]
    return db.execute("INSERT INTO carts (customer_id) VALUES (?)", (customer_id,))


def lines_for_cart(cart_id: int) -> list[dict]:
    return db.query(
        """
        SELECT ci.*, b.title, b.author, b.slug, e.format
        FROM cart_items ci
        JOIN editions e ON e.id = ci.edition_id
        JOIN books b ON b.id = e.book_id
        WHERE ci.cart_id = ?
        ORDER BY ci.id
        """,
        (cart_id,),
    )


def add_item(cart_id: int, edition_id: int, quantity: int, unit_price_cents: int) -> None:
    db.execute(
        """
        INSERT INTO cart_items (cart_id, edition_id, quantity, unit_price_cents)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(cart_id, edition_id) DO UPDATE
        SET quantity = quantity + excluded.quantity
        """,
        (cart_id, edition_id, quantity, unit_price_cents),
    )


def remove_item(cart_id: int, edition_id: int) -> None:
    db.execute(
        "DELETE FROM cart_items WHERE cart_id = ? AND edition_id = ?",
        (cart_id, edition_id),
    )


def mark_converted(cart_id: int) -> None:
    db.execute(
        "UPDATE carts SET status = 'converted', updated_at = datetime('now') WHERE id = ?",
        (cart_id,),
    )
