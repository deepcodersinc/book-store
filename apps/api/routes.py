"""Public machine-facing endpoints.

Everything here is reachable from the internet without a session:

  GET  /api/v1/books        published catalogue feed, consumed by partners
  POST /webhooks/stripe     payment confirmations, verified by signature
  GET  /download/{token}    purchased ebook, gated by a one-off token

The catalogue feed is a published contract — its response shape cannot change
without breaking the integrations that read it.
"""

from datetime import datetime

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from integrations import storage
from services.catalog import service as catalog
from services.fulfillment import service as fulfillment
from services.payments import service as payments

router = APIRouter()


@router.get("/api/v1/books")
async def partner_catalogue(q: str | None = None, limit: int = 50):
    """Published catalogue feed. Stable contract — additive changes only."""
    books = catalog.browse(search=q, limit=min(limit, 100))
    return {
        "count": len(books),
        "books": [
            {
                "slug": book.slug,
                "title": book.title,
                "author": book.author,
                "published_year": book.published_year,
                "cover_url": catalog.cover_url(book),
                "editions": [
                    {
                        "format": edition.format.value,
                        "price_cents": edition.price_cents,
                        "currency": edition.currency,
                        "isbn": edition.isbn,
                        "available": edition.in_stock,
                    }
                    for edition in book.editions
                ],
            }
            for book in books
        ],
    }


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Payment confirmation from Stripe. Public, but signature-verified."""
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    try:
        result = payments.handle_webhook(payload, signature)
    except payments.PaymentError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    return result


@router.get("/download/{token}")
async def download(token: str):
    """Serve a purchased ebook. The token is the only thing protecting this."""
    grant = fulfillment.get_download_grant(token)
    if grant is None:
        return JSONResponse({"error": "Unknown or expired download link"}, status_code=404)

    if grant["download_count"] >= grant["max_downloads"]:
        return JSONResponse({"error": "Download limit reached"}, status_code=410)

    if datetime.fromisoformat(grant["expires_at"]) < datetime.utcnow():
        return JSONResponse({"error": "This link has expired"}, status_code=410)

    if not grant["asset_path"] or not storage.exists(grant["asset_path"]):
        return JSONResponse({"error": "File is not available"}, status_code=404)

    content = storage.read_bytes(grant["asset_path"])
    fulfillment.record_download(grant["id"])
    filename = grant["asset_path"].rsplit("/", 1)[-1]
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
