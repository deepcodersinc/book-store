"""Shipments, download grants and the job queue. Owned by the fulfilment worker."""

import json

from data import db


# ── Jobs ────────────────────────────────────────────────────────────────────

def enqueue(job_type: str, payload: dict) -> int:
    return db.execute(
        "INSERT INTO jobs (type, payload) VALUES (?, ?)",
        (job_type, json.dumps(payload)),
    )


def claim_next(job_type: str | None = None) -> dict | None:
    """Take the oldest queued job and mark it running."""
    if job_type:
        row = db.query_one(
            "SELECT * FROM jobs WHERE status = 'queued' AND type = ? ORDER BY id LIMIT 1",
            (job_type,),
        )
    else:
        row = db.query_one("SELECT * FROM jobs WHERE status = 'queued' ORDER BY id LIMIT 1")
    if not row:
        return None
    db.execute(
        "UPDATE jobs SET status = 'running', attempts = attempts + 1 WHERE id = ?",
        (row["id"],),
    )
    row["payload"] = json.loads(row["payload"])
    return row


def complete(job_id: int) -> None:
    db.execute(
        "UPDATE jobs SET status = 'done', processed_at = datetime('now') WHERE id = ?",
        (job_id,),
    )


def fail(job_id: int, error: str) -> None:
    db.execute(
        """
        UPDATE jobs SET status = 'failed', last_error = ?, processed_at = datetime('now')
        WHERE id = ?
        """,
        (error, job_id),
    )


def pending_jobs() -> list[dict]:
    return db.query("SELECT * FROM jobs WHERE status IN ('queued','running') ORDER BY id")


def all_jobs(limit: int = 50) -> list[dict]:
    return db.query("SELECT * FROM jobs ORDER BY id DESC LIMIT ?", (limit,))


# ── Physical fulfilment ─────────────────────────────────────────────────────

def create_shipment(order_id: int, tracking_number: str, carrier: str = "demo-post") -> int:
    return db.execute(
        "INSERT INTO shipments (order_id, carrier, tracking_number) VALUES (?, ?, ?)",
        (order_id, carrier, tracking_number),
    )


def shipments_for_order(order_id: int) -> list[dict]:
    return db.query("SELECT * FROM shipments WHERE order_id = ?", (order_id,))


# ── Digital fulfilment ──────────────────────────────────────────────────────

def create_download(order_item_id: int, token: str, expires_at: str,
                    max_downloads: int) -> int:
    return db.execute(
        """
        INSERT INTO downloads (order_item_id, token, expires_at, max_downloads)
        VALUES (?, ?, ?, ?)
        """,
        (order_item_id, token, expires_at, max_downloads),
    )


def get_download(token: str) -> dict | None:
    return db.query_one(
        """
        SELECT d.*, oi.edition_id, e.asset_path, b.title
        FROM downloads d
        JOIN order_items oi ON oi.id = d.order_item_id
        JOIN editions e ON e.id = oi.edition_id
        JOIN books b ON b.id = e.book_id
        WHERE d.token = ?
        """,
        (token,),
    )


def downloads_for_order(order_id: int) -> list[dict]:
    return db.query(
        """
        SELECT d.*, b.title
        FROM downloads d
        JOIN order_items oi ON oi.id = d.order_item_id
        JOIN editions e ON e.id = oi.edition_id
        JOIN books b ON b.id = e.book_id
        WHERE oi.order_id = ?
        """,
        (order_id,),
    )


def record_download(download_id: int) -> None:
    db.execute(
        "UPDATE downloads SET download_count = download_count + 1 WHERE id = ?",
        (download_id,),
    )
