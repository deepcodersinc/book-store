"""Catalogue reads and writes. Owned by the catalog service."""

from data import db


# Orderings the listing supports. Never interpolate anything else into the
# query — the caller's sort key only ever selects one of these clauses.
# Books with no edition have no price, so they sort last either way, and every
# clause breaks ties on title to keep the order stable.
SORT_CLAUSES = {
    "title_asc": "lower(b.title)",
    "author_asc": "lower(b.author), lower(b.title)",
    "price_asc": "min_price_cents IS NULL, min_price_cents ASC, lower(b.title)",
    "price_desc": "min_price_cents IS NULL, min_price_cents DESC, lower(b.title)",
}

DEFAULT_SORT = "title_asc"


def list_books(search: str | None = None, limit: int = 50,
               sort: str = DEFAULT_SORT) -> list[dict]:
    """Catalogue listing. Sorting happens here, before the limit, so a price
    ordering surfaces the cheapest books in the shop rather than reshuffling
    the alphabetically first ones."""
    order_by = SORT_CLAUSES.get(sort, SORT_CLAUSES[DEFAULT_SORT])
    price = "(SELECT MIN(price_cents) FROM editions e WHERE e.book_id = b.id)"
    if search:
        pattern = f"%{search.lower()}%"
        return db.query(
            f"""
            SELECT b.*, {price} AS min_price_cents
            FROM books b
            WHERE lower(b.title) LIKE ? OR lower(b.author) LIKE ?
            ORDER BY {order_by} LIMIT ?
            """,
            (pattern, pattern, limit),
        )
    return db.query(
        f"""
        SELECT b.*, {price} AS min_price_cents
        FROM books b
        ORDER BY {order_by} LIMIT ?
        """,
        (limit,),
    )


def get_book(book_id: int) -> dict | None:
    return db.query_one("SELECT * FROM books WHERE id = ?", (book_id,))


def get_book_by_slug(slug: str) -> dict | None:
    return db.query_one("SELECT * FROM books WHERE slug = ?", (slug,))


def editions_for_book(book_id: int) -> list[dict]:
    """Editions joined with stock so callers can tell what is actually available."""
    return db.query(
        """
        SELECT e.*, i.on_hand
        FROM editions e
        LEFT JOIN inventory i ON i.edition_id = e.id
        WHERE e.book_id = ?
        ORDER BY e.price_cents
        """,
        (book_id,),
    )


def get_edition(edition_id: int) -> dict | None:
    return db.query_one(
        """
        SELECT e.*, i.on_hand, b.title, b.author, b.slug
        FROM editions e
        JOIN books b ON b.id = e.book_id
        LEFT JOIN inventory i ON i.edition_id = e.id
        WHERE e.id = ?
        """,
        (edition_id,),
    )


def update_book(book_id: int, title: str, author: str, description: str) -> None:
    db.execute(
        """
        UPDATE books
        SET title = ?, author = ?, description = ?, updated_at = datetime('now')
        WHERE id = ?
        """,
        (title, author, description, book_id),
    )


def create_book(slug: str, title: str, author: str, description: str,
                published_year: int | None, cover_path: str | None) -> int:
    return db.execute(
        """
        INSERT INTO books (slug, title, author, description, published_year, cover_path)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (slug, title, author, description, published_year, cover_path),
    )


def create_edition(book_id: int, fmt: str, price_cents: int,
                   isbn: str | None, asset_path: str | None) -> int:
    return db.execute(
        """
        INSERT INTO editions (book_id, format, price_cents, isbn, asset_path)
        VALUES (?, ?, ?, ?, ?)
        """,
        (book_id, fmt, price_cents, isbn, asset_path),
    )


def count_books() -> int:
    row = db.query_one("SELECT COUNT(*) AS n FROM books")
    return row["n"] if row else 0
