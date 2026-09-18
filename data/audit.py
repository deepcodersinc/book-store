"""Audit trail for staff actions. Written by the admin console."""

import json

from data import db


def record(actor: str, action: str, entity_type: str, entity_id: str,
           detail: dict | None = None) -> int:
    return db.execute(
        """
        INSERT INTO audit_log (actor, action, entity_type, entity_id, detail)
        VALUES (?, ?, ?, ?, ?)
        """,
        (actor, action, entity_type, str(entity_id), json.dumps(detail or {})),
    )


def list_recent(limit: int = 50) -> list[dict]:
    return db.query("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,))
