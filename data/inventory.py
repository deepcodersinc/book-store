"""Stock levels for physical editions. Owned by the inventory service."""

from data import db


def get_stock(edition_id: int) -> dict | None:
    return db.query_one("SELECT * FROM inventory WHERE edition_id = ?", (edition_id,))


def set_stock(edition_id: int, on_hand: int, reorder_threshold: int = 3) -> None:
    db.execute(
        """
        INSERT INTO inventory (edition_id, on_hand, reorder_threshold)
        VALUES (?, ?, ?)
        ON CONFLICT(edition_id) DO UPDATE
        SET on_hand = excluded.on_hand, updated_at = datetime('now')
        """,
        (edition_id, on_hand, reorder_threshold),
    )


def decrement(edition_id: int, quantity: int) -> bool:
    """Take stock off the shelf. Returns False when there is not enough."""
    row = get_stock(edition_id)
    if row is None or row["on_hand"] < quantity:
        return False
    db.execute(
        """
        UPDATE inventory
        SET on_hand = on_hand - ?, updated_at = datetime('now')
        WHERE edition_id = ?
        """,
        (quantity, edition_id),
    )
    return True


def restock(edition_id: int, quantity: int) -> None:
    db.execute(
        """
        UPDATE inventory
        SET on_hand = on_hand + ?, updated_at = datetime('now')
        WHERE edition_id = ?
        """,
        (quantity, edition_id),
    )


def below_threshold() -> list[dict]:
    return db.query(
        """
        SELECT i.*, b.title, e.format
        FROM inventory i
        JOIN editions e ON e.id = i.edition_id
        JOIN books b ON b.id = e.book_id
        WHERE i.on_hand <= i.reorder_threshold
        ORDER BY i.on_hand
        """
    )


def all_stock() -> list[dict]:
    return db.query(
        """
        SELECT i.*, b.title, e.format
        FROM inventory i
        JOIN editions e ON e.id = i.edition_id
        JOIN books b ON b.id = e.book_id
        ORDER BY b.title
        """
    )
