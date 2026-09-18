"""Audit trail for staff actions.

Thin, but it exists so the web layer never writes to a repository directly.
"""

from data import audit as audit_repo


def record(actor: str, action: str, entity_type: str, entity_id, detail: dict | None = None) -> int:
    return audit_repo.record(actor, action, entity_type, entity_id, detail)


def recent(limit: int = 50) -> list[dict]:
    return audit_repo.list_recent(limit)
