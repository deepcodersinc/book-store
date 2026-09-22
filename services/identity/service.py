"""Accounts, sign-in and sessions.

Almost every other flow depends on this module to know who is asking.
"""

import hashlib
import re
import secrets
from datetime import datetime, timedelta

import settings
from data import customers as customer_repo
from packages.schemas.models import Customer

SESSION_TTL_DAYS = 14
DEMO_PASSWORD = "demo"

# Deliberately permissive: shoppers write numbers with spaces, dashes and
# brackets, and this shop sells across borders. Anything that reduces to a
# plausible run of digits is kept, in the shape the carrier wants it.
_MOBILE_PUNCTUATION = re.compile(r"[\s().-]")
_MOBILE_SHAPE = re.compile(r"^\+?\d{7,15}$")


def hash_password(password: str) -> str:
    salted = f"{settings.SESSION_SECRET}:{password}".encode()
    return hashlib.sha256(salted).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return secrets.compare_digest(hash_password(password), password_hash)


class IdentityError(ValueError):
    pass


def _to_customer(row: dict) -> Customer:
    return Customer(
        id=row["id"],
        email=row["email"],
        name=row["name"],
        country_code=row.get("country_code", "US"),
        mobile_number=row.get("mobile_number") or None,
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def normalise_mobile(raw: str) -> str | None:
    """Tidy a number as typed. None means the customer cleared the field."""
    cleaned = _MOBILE_PUNCTUATION.sub("", raw or "")
    if not cleaned:
        return None
    if not _MOBILE_SHAPE.match(cleaned):
        raise IdentityError("That does not look like a mobile number.")
    return cleaned


def set_mobile_number(customer_id: int, raw: str) -> str | None:
    """Store a mobile number for texts, or clear it when given nothing."""
    mobile = normalise_mobile(raw)
    customer_repo.set_mobile_number(customer_id, mobile)
    return mobile


def mobile_for_customer(customer_id: int | None) -> str | None:
    """The number to text, if this order belongs to an account that has one."""
    if customer_id is None:
        return None
    row = customer_repo.get_customer(customer_id)
    return (row or {}).get("mobile_number") or None


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
