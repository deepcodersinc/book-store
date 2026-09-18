"""Form parsing.

Reads urlencoded bodies with the standard library so the app has no dependency
on a multipart parser — nothing here uploads files.
"""

from urllib.parse import parse_qs

from fastapi import Request


async def form_data(request: Request) -> dict[str, str]:
    raw = await request.body()
    parsed = parse_qs(raw.decode("utf-8"), keep_blank_values=True)
    return {key: values[-1] for key, values in parsed.items()}


def as_int(values: dict[str, str], key: str, default: int = 0) -> int:
    try:
        return int(values.get(key, default))
    except (TypeError, ValueError):
        return default
