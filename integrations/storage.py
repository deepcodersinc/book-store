"""Object storage for cover images and ebook files.

Keys are stored in the database, never URLs, so the same row works whether the
bytes sit on local disk or in a bucket. Without S3_BUCKET this resolves to the
local filesystem.
"""

from pathlib import Path

import settings


def is_live() -> bool:
    return bool(settings.S3_BUCKET)


def public_url(key: str) -> str:
    """Browser-facing URL for a public object such as a cover image."""
    if is_live():
        endpoint = settings.S3_ENDPOINT or f"https://{settings.S3_BUCKET}.s3.amazonaws.com"
        return f"{endpoint}/{key}"
    return f"/static/{key}"


def local_path(key: str) -> Path:
    """Filesystem location of a private object such as an ebook file."""
    return settings.ASSETS_DIR / key


def exists(key: str) -> bool:
    if is_live():
        return True  # trusting the bucket; a real client would HEAD the object
    return local_path(key).exists()


def read_bytes(key: str) -> bytes:
    if is_live():
        raise NotImplementedError("Bucket reads are not configured in this environment")
    return local_path(key).read_bytes()
