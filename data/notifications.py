"""Outbox. Owned by the notification service; the admin console reads it."""

from data import db


def record(type_: str, recipient: str, subject: str, body: str,
           channel: str = "email", status: str = "sent") -> int:
    return db.execute(
        """
        INSERT INTO notifications (type, channel, recipient, subject, body, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (type_, channel, recipient, subject, body, status),
    )


def list_recent(limit: int = 50) -> list[dict]:
    return db.query("SELECT * FROM notifications ORDER BY id DESC LIMIT ?", (limit,))


def for_recipient(recipient: str) -> list[dict]:
    return db.query(
        "SELECT * FROM notifications WHERE recipient = ? ORDER BY id DESC",
        (recipient,),
    )
