"""Stock levels for physical editions.

Digital editions never run out, so everything here is a no-op for ebooks.
"""

from data import inventory as inventory_repo


def can_fulfil(edition_id: int, quantity: int) -> bool:
    stock = inventory_repo.get_stock(edition_id)
    if stock is None:
        return True  # no stock row means a digital edition
    return stock["on_hand"] >= quantity


def reserve(edition_id: int, quantity: int) -> bool:
    return inventory_repo.decrement(edition_id, quantity)


def release(edition_id: int, quantity: int) -> None:
    inventory_repo.restock(edition_id, quantity)


def level(edition_id: int) -> int | None:
    stock = inventory_repo.get_stock(edition_id)
    return stock["on_hand"] if stock else None


def needs_reordering() -> list[dict]:
    return inventory_repo.below_threshold()


def snapshot() -> list[dict]:
    return inventory_repo.all_stock()


def reconcile() -> dict:
    """Nightly sweep: report anything at or below its reorder threshold."""
    low = inventory_repo.below_threshold()
    return {
        "checked": len(inventory_repo.all_stock()),
        "below_threshold": len(low),
        "titles": [row["title"] for row in low],
    }
