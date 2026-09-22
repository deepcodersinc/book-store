"""Runtime configuration for the bookstore.

Every integration with a third party can run in mock mode so the app boots with
no external services. Set the corresponding env var to switch to the real thing.
"""

import os
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{ROOT / 'bookstore.db'}")

SEED_FILE = ROOT / "seed" / "books.json"
STATIC_DIR = ROOT / "static"
ASSETS_DIR = ROOT / "assets"

# Third-party integrations. Without credentials these fall back to local mocks.
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")

# Object storage for covers and ebook files. Falls back to the local filesystem.
S3_BUCKET = os.getenv("S3_BUCKET", "")
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "")

SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-secret-not-for-production")

# Accounts opened before this date are still on the original pricing agreement.
LEGACY_PRICING_CUTOFF = date(2019, 1, 1)

# Rollout flag for the rewritten checkout. The old path stays until it is retired.
FEATURE_NEW_CHECKOUT = os.getenv("FEATURE_NEW_CHECKOUT", "false").lower() == "true"

EU_COUNTRIES = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR",
    "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK",
    "SI", "ES", "SE",
}

VAT_RATE = 0.20
DOWNLOAD_EXPIRY_HOURS = 72
MAX_DOWNLOADS_PER_PURCHASE = 5
