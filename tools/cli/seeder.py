"""Loads the demo catalogue, accounts and order history.

The accounts are deliberately shaped: one opened before the legacy pricing
cutoff, one in the EU, one ordinary. Between them they exercise every pricing
branch without anyone having to contrive a scenario during a demo.
"""

import json
from datetime import datetime, timedelta

import settings
from data import books as book_repo
from data import customers as customer_repo
from data import inventory as inventory_repo
from data import orders as order_repo
from data import payments as payment_repo
from services.identity import service as identity

DEMO_ACCOUNTS = [
    # (email, name, country, account age in days)
    ("ada@example.com", "Ada Whitfield", "US", 220),
    ("jonas@example.de", "Jonas Kessler", "DE", 400),      # EU -> VAT applies
    ("marie@example.fr", "Marie Delacroix", "FR", 3200),   # EU and legacy pricing
    ("sam@example.com", "Sam Okafor", "US", 2900),         # legacy pricing
    ("priya@example.com", "Priya Raman", "US", 40),
]


def _load_catalogue() -> list[dict]:
    with open(settings.SEED_FILE, encoding="utf-8") as handle:
        return json.load(handle)


def _seed_books() -> tuple[int, int]:
    books = _load_catalogue()
    edition_count = 0
    for entry in books:
        book_id = book_repo.create_book(
            slug=entry["slug"],
            title=entry["title"],
            author=entry["author"],
            description=entry["description"],
            published_year=entry.get("published_year"),
            cover_path=f"covers/{entry['slug']}.svg",
        )
        for edition in entry["editions"]:
            asset = edition.get("asset_path")
            edition_id = book_repo.create_edition(
                book_id=book_id,
                fmt=edition["format"],
                price_cents=edition["price_cents"],
                isbn=edition.get("isbn"),
                asset_path=asset,
            )
            edition_count += 1
            # Digital editions never run out, so they get no stock row at all.
            if edition["format"] != "ebook":
                inventory_repo.set_stock(edition_id, edition.get("on_hand", 8))
    return len(books), edition_count


def _seed_customers() -> int:
    password_hash = identity.hash_password(identity.DEMO_PASSWORD)
    for email, name, country, age_days in DEMO_ACCOUNTS:
        created = (datetime.utcnow() - timedelta(days=age_days)).isoformat(" ", "seconds")
        customer_repo.create_customer(email, name, password_hash, country, created)
    return len(DEMO_ACCOUNTS)


def _seed_orders() -> int:
    """A short order history covering both formats and both pricing schemes."""
    customers = customer_repo.list_customers()
    if not customers:
        return 0

    made = 0
    plans = [
        # (customer index, [(edition offset, quantity)], status)
        (0, [(0, 1)], "fulfilled"),
        (1, [(1, 2)], "paid"),
        (2, [(2, 1), (3, 1)], "fulfilled"),
        (3, [(4, 1)], "pending"),
        (0, [(5, 3)], "paid"),
    ]

    all_editions = []
    for book in book_repo.list_books(limit=100):
        all_editions.extend(book_repo.editions_for_book(book["id"]))
    if not all_editions:
        return 0

    for customer_index, lines, status in plans:
        customer = customers[customer_index % len(customers)]
        subtotal = 0
        chosen = []
        for offset, quantity in lines:
            edition = all_editions[offset % len(all_editions)]
            subtotal += edition["price_cents"] * quantity
            chosen.append((edition, quantity))

        created = datetime.fromisoformat(customer["created_at"])
        is_legacy = created.date() < settings.LEGACY_PRICING_CUTOFF
        scheme = "legacy" if is_legacy else "standard"
        discount = int(subtotal * (0.15 if is_legacy else 0))
        taxable = subtotal - discount
        tax = int(taxable * settings.VAT_RATE) if customer["country_code"] in settings.EU_COUNTRIES else 0

        order_id = order_repo.create_order(
            order_number=order_repo.next_order_number(),
            customer_id=customer["id"],
            email=customer["email"],
            subtotal_cents=subtotal,
            discount_cents=discount,
            tax_cents=tax,
            total_cents=taxable + tax,
            country_code=customer["country_code"],
            pricing_scheme=scheme,
            checkout_version="v1",
        )
        for edition, quantity in chosen:
            order_repo.add_order_item(
                order_id, edition["id"], quantity, edition["price_cents"], edition["format"])

        # Checkout always records a payment attempt, so seeded orders do too.
        payment_id = payment_repo.create_payment(
            order_id, taxable + tax, f"ch_seed_{order_id}")
        if status != "pending":
            payment_repo.set_status(payment_id, "succeeded")
        order_repo.set_status(order_id, status)
        made += 1

    return made


def run() -> dict:
    books, editions = _seed_books()
    customers = _seed_customers()
    orders = _seed_orders()
    return {"books": books, "editions": editions,
            "customers": customers, "orders": orders}
