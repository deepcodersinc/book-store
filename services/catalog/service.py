"""Catalogue service.

Everything that needs book data goes through here. The web layer must never
query the catalogue tables itself — availability, pricing display and cover
resolution all depend on rules that live in this module.
"""

from data import books as book_repo
from integrations import storage
from packages.schemas.models import Book, Edition, EditionFormat


def _to_edition(row: dict) -> Edition:
    return Edition(
        id=row["id"],
        book_id=row["book_id"],
        format=EditionFormat(row["format"]),
        price_cents=row["price_cents"],
        currency=row.get("currency", "USD"),
        isbn=row.get("isbn"),
        asset_path=row.get("asset_path"),
        on_hand=row.get("on_hand"),
    )


def _to_book(row: dict, editions: list[dict] | None = None) -> Book:
    return Book(
        id=row["id"],
        slug=row["slug"],
        title=row["title"],
        author=row["author"],
        description=row.get("description", ""),
        published_year=row.get("published_year"),
        cover_path=row.get("cover_path"),
        editions=[_to_edition(e) for e in (editions or [])],
    )


# How a shopper may order the listing, in the order the choices are offered.
SORT_OPTIONS = [
    ("title_asc", "Name, A–Z"),
    ("author_asc", "Author, A–Z"),
    ("price_asc", "Price, low to high"),
    ("price_desc", "Price, high to low"),
]

DEFAULT_SORT = book_repo.DEFAULT_SORT


def normalise_sort(sort: str | None) -> str:
    """Fall back to the default rather than erroring on an unknown ordering."""
    keys = {key for key, _ in SORT_OPTIONS}
    return sort if sort in keys else DEFAULT_SORT


def browse(search: str | None = None, limit: int = 50,
           sort: str = DEFAULT_SORT) -> list[Book]:
    """Catalogue listing, with editions attached so prices can be shown."""
    rows = book_repo.list_books(search=search, limit=limit,
                                sort=normalise_sort(sort))
    return [_to_book(row, book_repo.editions_for_book(row["id"])) for row in rows]


def get_by_slug(slug: str) -> Book | None:
    row = book_repo.get_book_by_slug(slug)
    if not row:
        return None
    return _to_book(row, book_repo.editions_for_book(row["id"]))


def get_by_id(book_id: int) -> Book | None:
    row = book_repo.get_book(book_id)
    if not row:
        return None
    return _to_book(row, book_repo.editions_for_book(book_id))


def get_edition(edition_id: int) -> dict | None:
    """Edition joined with its book, for callers building a cart or order line."""
    return book_repo.get_edition(edition_id)


def cover_url(book: Book) -> str:
    if not book.cover_path:
        return "/static/covers/placeholder.svg"
    return storage.public_url(book.cover_path)


def update_details(book_id: int, title: str, author: str, description: str) -> None:
    book_repo.update_book(book_id, title, author, description)


def catalogue_size() -> int:
    return book_repo.count_books()
