"""Catalogue reads and writes. Owned by the catalog service."""

from data import db


def list_books(search: str | None = None, limit: int = 50) -> list[dict]:
    if search:
        pattern = f"%{search.lower()}%"
        return db.query(
            """
            SELECT * FROM books
            WHERE lower(title) LIKE ? OR lower(author) LIKE ?
            ORDER BY title LIMIT ?
            """,
            (pattern, pattern, limit),
        )
    return db.query("SELECT * FROM books ORDER BY title LIMIT ?", (limit,))


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
