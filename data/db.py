"""SQLite connection handling and schema definition.

The whole catalogue, order book and job queue live in one file-backed database.
Nothing outside `data/` should import this module — services talk to the
repositories, and the web layer talks to services.
"""

import sqlite3
from pathlib import Path

import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS books (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    slug            TEXT NOT NULL UNIQUE,
    title           TEXT NOT NULL,
    author          TEXT NOT NULL,
    description     TEXT NOT NULL DEFAULT '',
    published_year  INTEGER,
    cover_path      TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS editions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id      INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    format       TEXT NOT NULL CHECK (format IN ('hardcover','paperback','ebook')),
    price_cents  INTEGER NOT NULL,
    currency     TEXT NOT NULL DEFAULT 'USD',
    isbn         TEXT,
    asset_path   TEXT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (book_id, format)
);

-- Physical editions only; a digital edition never runs out.
CREATE TABLE IF NOT EXISTS inventory (
    edition_id        INTEGER PRIMARY KEY REFERENCES editions(id) ON DELETE CASCADE,
    on_hand           INTEGER NOT NULL DEFAULT 0,
    reserved          INTEGER NOT NULL DEFAULT 0,
    reorder_threshold INTEGER NOT NULL DEFAULT 3,
    updated_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS customers (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT NOT NULL UNIQUE,
    name          TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    country_code  TEXT NOT NULL DEFAULT 'US',
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at  TEXT NOT NULL
);

-- Carts belonging to signed-in shoppers. Guest carts live in a signed cookie
-- and never reach the database.
CREATE TABLE IF NOT EXISTS carts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    status      TEXT NOT NULL DEFAULT 'active'
                CHECK (status IN ('active','converted','abandoned')),
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS cart_items (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    cart_id          INTEGER NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
    edition_id       INTEGER NOT NULL REFERENCES editions(id),
    quantity         INTEGER NOT NULL DEFAULT 1,
    unit_price_cents INTEGER NOT NULL,
    UNIQUE (cart_id, edition_id)
);

CREATE TABLE IF NOT EXISTS orders (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number     TEXT NOT NULL UNIQUE,
    customer_id      INTEGER REFERENCES customers(id),
    email            TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending','paid','fulfilled','cancelled','refunded')),
    subtotal_cents   INTEGER NOT NULL,
    discount_cents   INTEGER NOT NULL DEFAULT 0,
    tax_cents        INTEGER NOT NULL DEFAULT 0,
    total_cents      INTEGER NOT NULL,
    currency         TEXT NOT NULL DEFAULT 'USD',
    country_code     TEXT NOT NULL DEFAULT 'US',
    -- Which pricing rules and which checkout implementation produced this order.
    pricing_scheme   TEXT NOT NULL DEFAULT 'standard'
                     CHECK (pricing_scheme IN ('standard','legacy')),
    checkout_version TEXT NOT NULL DEFAULT 'v1' CHECK (checkout_version IN ('v1','v2')),
    created_at       TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS order_items (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id           INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    edition_id         INTEGER NOT NULL REFERENCES editions(id),
    quantity           INTEGER NOT NULL DEFAULT 1,
    unit_price_cents   INTEGER NOT NULL,
    format             TEXT NOT NULL,
    fulfillment_status TEXT NOT NULL DEFAULT 'pending'
                       CHECK (fulfillment_status IN ('pending','shipped','delivered','downloadable'))
);

CREATE TABLE IF NOT EXISTS payments (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id     INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    provider     TEXT NOT NULL DEFAULT 'stripe',
    provider_ref TEXT,
    amount_cents INTEGER NOT NULL,
    status       TEXT NOT NULL DEFAULT 'pending'
                 CHECK (status IN ('pending','succeeded','failed')),
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS refunds (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_id      INTEGER NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
    order_item_id   INTEGER REFERENCES order_items(id),
    amount_cents    INTEGER NOT NULL,
    reason          TEXT NOT NULL DEFAULT '',
    -- Physical goods have to come back before the refund settles.
    requires_return INTEGER NOT NULL DEFAULT 0,
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','awaiting_return','settled','rejected')),
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS shipments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id        INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    carrier         TEXT NOT NULL DEFAULT 'demo-post',
    tracking_number TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'in_transit',
    shipped_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS downloads (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    order_item_id  INTEGER NOT NULL REFERENCES order_items(id) ON DELETE CASCADE,
    token          TEXT NOT NULL UNIQUE,
    expires_at     TEXT NOT NULL,
    download_count INTEGER NOT NULL DEFAULT 0,
    max_downloads  INTEGER NOT NULL DEFAULT 5,
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Stands in for a message broker. The fulfilment worker drains this table.
CREATE TABLE IF NOT EXISTS jobs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    type         TEXT NOT NULL,
    payload      TEXT NOT NULL DEFAULT '{}',
    status       TEXT NOT NULL DEFAULT 'queued'
                 CHECK (status IN ('queued','running','done','failed')),
    attempts     INTEGER NOT NULL DEFAULT 0,
    last_error   TEXT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    processed_at TEXT
);

-- Outbox. Nothing is actually emailed; the admin console reads this table.
CREATE TABLE IF NOT EXISTS notifications (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    type      TEXT NOT NULL,
    channel   TEXT NOT NULL DEFAULT 'email',
    recipient TEXT NOT NULL,
    subject   TEXT NOT NULL,
    body      TEXT NOT NULL,
    status    TEXT NOT NULL DEFAULT 'sent',
    sent_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    actor       TEXT NOT NULL,
    action      TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id   TEXT NOT NULL,
    detail      TEXT NOT NULL DEFAULT '{}',
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_editions_book ON editions(book_id);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
"""


def database_path() -> Path:
    """Filesystem path behind DATABASE_URL."""
    url = settings.DATABASE_URL
    if url.startswith("sqlite:///"):
        return Path(url[len("sqlite:///"):])
    raise ValueError(f"Unsupported DATABASE_URL: {url}")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(database_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)


def query(sql: str, params: tuple = ()) -> list[dict]:
    with connect() as conn:
        return [dict(row) for row in conn.execute(sql, params).fetchall()]


def query_one(sql: str, params: tuple = ()) -> dict | None:
    rows = query(sql, params)
    return rows[0] if rows else None


def execute(sql: str, params: tuple = ()) -> int:
    """Run a write and return the last inserted row id."""
    with connect() as conn:
        cursor = conn.execute(sql, params)
        conn.commit()
        return cursor.lastrowid


def execute_many(statements: list[tuple[str, tuple]]) -> None:
    """Run several writes in one transaction."""
    with connect() as conn:
        for sql, params in statements:
            conn.execute(sql, params)
        conn.commit()
