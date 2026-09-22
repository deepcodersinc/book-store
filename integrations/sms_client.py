"""Text messages through Twilio.

Without TWILIO_AUTH_TOKEN nothing leaves the machine — the notification service
still records every message, and the admin console shows them as an outbox.
"""

import settings

# Longer texts are split into several billable parts by the carrier, so callers
# keep shipping messages short rather than relying on this.
MAX_LENGTH = 320


class SmsError(RuntimeError):
    pass


def is_live() -> bool:
    return bool(settings.TWILIO_AUTH_TOKEN)


def send(to: str, body: str) -> dict:
    """Deliver a text. In mock mode this is a no-op that reports success."""
    if not is_live():
        return {"accepted": True, "provider": "mock", "to": to,
                "from": settings.TWILIO_FROM_NUMBER or "+10000000000"}

    # Real call would go through the Twilio SDK here.
    raise SmsError("Live Twilio calls are not configured in this environment")
