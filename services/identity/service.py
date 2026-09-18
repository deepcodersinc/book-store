"""Accounts, sign-in and sessions.

Almost every other flow depends on this module to know who is asking.
"""

import hashlib
import secrets
from datetime import datetime, timedelta

import settings
from data import customers as customer_repo
from packages.schemas.models import Customer

SESSION_TTL_DAYS = 14
DEMO_PASSWORD = "demo"


def hash_password(password: str) -> str:
    salted = f"{settings.SESSION_SECRET}:{password}".encode()
    return hashlib.sha256(salted).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return secrets.compare_digest(hash_password(password), password_hash)


def _to_customer(row: dict) -> Customer:
    return Customer(
        id=row["id"],
        email=row["email"],
        name=row["name"],
        country_code=row.get("country_code", "US"),
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def authenticate(email: str, password: str) -> Customer | None:
    row = customer_repo.get_by_email(email)
    if not row or not verify_password(password, row["password_hash"]):
        return None
    return _to_customer(row)


def start_session(customer_id: int | None) -> str:
    session_id = secrets.token_urlsafe(24)
    expires = (datetime.utcnow() + timedelta(days=SESSION_TTL_DAYS)).isoformat(" ", "seconds")
    customer_repo.create_session(session_id, customer_id, expires)
    return session_id


def end_session(session_id: str) -> None:
    customer_repo.delete_session(session_id)


def current_customer(session_id: str | None) -> Customer | None:
    """Resolve a session cookie to an account. None means a guest."""
    if not session_id:
        return None
    session = customer_repo.get_session(session_id)
    if not session or session["customer_id"] is None:
        return None
    row = customer_repo.get_customer(session["customer_id"])
    return _to_customer(row) if row else None


def get_customer(customer_id: int) -> Customer | None:
    row = customer_repo.get_customer(customer_id)
    return _to_customer(row) if row else None


def is_legacy_account(customer: Customer) -> bool:
    """Accounts opened before the cutoff are still on the original agreement."""
    return customer.created_at.date() < settings.LEGACY_PRICING_CUTOFF


def list_customers() -> list[Customer]:
    return [_to_customer(row) for row in customer_repo.list_customers()]
