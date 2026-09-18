"""Accounts and sessions. Owned by the identity service."""

from data import db


def get_customer(customer_id: int) -> dict | None:
    return db.query_one("SELECT * FROM customers WHERE id = ?", (customer_id,))


def get_by_email(email: str) -> dict | None:
    return db.query_one("SELECT * FROM customers WHERE lower(email) = ?", (email.lower(),))


def create_customer(email: str, name: str, password_hash: str,
                    country_code: str = "US", created_at: str | None = None) -> int:
    if created_at:
        return db.execute(
            """
            INSERT INTO customers (email, name, password_hash, country_code, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (email, name, password_hash, country_code, created_at),
        )
    return db.execute(
        """
        INSERT INTO customers (email, name, password_hash, country_code)
        VALUES (?, ?, ?, ?)
        """,
        (email, name, password_hash, country_code),
    )


def list_customers() -> list[dict]:
    return db.query("SELECT * FROM customers ORDER BY created_at")


def create_session(session_id: str, customer_id: int | None, expires_at: str) -> None:
    db.execute(
        "INSERT INTO sessions (id, customer_id, expires_at) VALUES (?, ?, ?)",
        (session_id, customer_id, expires_at),
    )


def get_session(session_id: str) -> dict | None:
    return db.query_one(
        "SELECT * FROM sessions WHERE id = ? AND expires_at > datetime('now')",
        (session_id,),
    )


def delete_session(session_id: str) -> None:
    db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
