"""Transactional email through SendGrid.

Without SENDGRID_API_KEY nothing leaves the machine — the notification service
still records every message, and the admin console shows them as an outbox.
"""

import settings


class EmailError(RuntimeError):
    pass


def is_live() -> bool:
    return bool(settings.SENDGRID_API_KEY)


def send(to: str, subject: str, body: str) -> dict:
    """Deliver a message. In mock mode this is a no-op that reports success."""
    if not is_live():
        return {"accepted": True, "provider": "mock", "to": to}

    # Real call would go through the SendGrid SDK here.
    raise EmailError("Live SendGrid calls are not configured in this environment")
