"""Staff console.

Catalogue editing, order inspection, the notification outbox and the job queue.
Everything under /admin is staff-only.
"""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from packages.web import templating
from packages.web.forms import as_int, form_data
from services.audit import service as audit
from services.catalog import service as catalog
from services.fulfillment import service as fulfillment
from services.inventory import service as inventory
from services.notifications import service as notifications
from services.orders import service as orders
from services.payments import service as payments

router = APIRouter(prefix="/admin")
templates = templating.build(Path(__file__).parent / "templates")

STAFF_ACTOR = "staff@bookstore.example"


def _page(request: Request, template: str, **context) -> HTMLResponse:
    base = {"customer": None, "cart": None, "query": None}
    base.update(context)
    return templates.TemplateResponse(request, template, base)


@router.get("", response_class=HTMLResponse)
async def dashboard(request: Request):
    return _page(
        request, "dashboard.html",
        book_count=catalog.catalogue_size(),
        orders=orders.recent(limit=10),
        low_stock=inventory.needs_reordering(),
        pending_jobs=fulfillment.pending(),
    )


@router.get("/books", response_class=HTMLResponse)
async def book_list(request: Request):
    return _page(request, "books.html", books=catalog.browse(limit=100))


@router.get("/books/{slug}", response_class=HTMLResponse)
async def edit_book_form(request: Request, slug: str):
    book = catalog.get_by_slug(slug)
    if not book:
        return RedirectResponse("/admin/books", status_code=303)
    return _page(request, "book_edit.html", book=book)


@router.post("/books/{slug}")
async def edit_book(request: Request, slug: str):
    book = catalog.get_by_slug(slug)
    if not book:
        return RedirectResponse("/admin/books", status_code=303)

    values = await form_data(request)
    catalog.update_details(
        book.id,
        values.get("title", book.title),
        values.get("author", book.author),
        values.get("description", book.description),
    )
    audit.record(STAFF_ACTOR, "book.updated", "book", book.id,
                 {"slug": slug, "title": values.get("title")})
    return RedirectResponse(f"/admin/books/{slug}", status_code=303)


@router.get("/orders", response_class=HTMLResponse)
async def order_list(request: Request):
    return _page(request, "orders.html", orders=orders.recent(limit=100))


@router.get("/orders/{order_number}", response_class=HTMLResponse)
async def order_detail(request: Request, order_number: str):
    order = orders.get_by_number(order_number)
    if not order:
        return RedirectResponse("/admin/orders", status_code=303)
    return _page(request, "order_detail.html", order=order,
                 items=orders.items(order["id"]),
                 shipments=fulfillment.shipments_for_order(order["id"]),
                 downloads=fulfillment.downloads_for_order(order["id"]))


@router.post("/orders/{order_number}/confirm-payment")
async def confirm_payment(request: Request, order_number: str):
    """Replay the Stripe webhook locally so the flow can be driven by hand."""
    try:
        payments.confirm_locally(order_number)
    except payments.PaymentError:
        pass
    return RedirectResponse(f"/admin/orders/{order_number}", status_code=303)


@router.post("/orders/{order_number}/refund")
async def refund(request: Request, order_number: str):
    values = await form_data(request)
    try:
        payments.refund_item(as_int(values, "order_item_id"), values.get("reason", ""))
        audit.record(STAFF_ACTOR, "refund.opened", "order", order_number, values)
    except payments.PaymentError:
        pass
    return RedirectResponse(f"/admin/orders/{order_number}", status_code=303)


@router.get("/outbox", response_class=HTMLResponse)
async def outbox(request: Request):
    return _page(request, "outbox.html", messages=notifications.outbox(limit=100))


@router.get("/jobs", response_class=HTMLResponse)
async def jobs(request: Request):
    return _page(request, "jobs.html", jobs=fulfillment.recent(limit=100))


@router.get("/inventory", response_class=HTMLResponse)
async def stock(request: Request):
    return _page(request, "inventory.html", stock=inventory.snapshot())


@router.get("/audit", response_class=HTMLResponse)
async def audit_trail(request: Request):
    return _page(request, "audit.html", entries=audit.recent(limit=100))
