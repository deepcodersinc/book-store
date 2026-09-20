"""Shopper-facing pages.

Presentation only. Every piece of data on these pages comes from a service —
this module never touches the database directly.
"""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from packages.web import templating
from packages.web.forms import as_int, form_data
from services.catalog import service as catalog
from services.checkout import guest_cart
from services.checkout import service as checkout
from services.fulfillment import service as fulfillment
from services.identity import service as identity
from services.orders import service as orders

router = APIRouter()
templates = templating.build(Path(__file__).parent / "templates")

SESSION_COOKIE = "session_id"


def _viewer(request: Request):
    """Who is asking, and what is in their basket."""
    customer = identity.current_customer(request.cookies.get(SESSION_COOKIE))
    cart = checkout.load_cart(customer, request.cookies.get(guest_cart.COOKIE_NAME))
    return customer, cart


def _page(request: Request, template: str, **context) -> HTMLResponse:
    customer, cart = _viewer(request)
    base = {"customer": customer, "cart": cart, "query": None}
    base.update(context)
    return templates.TemplateResponse(request, template, base)


# ── Browsing ────────────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def home(request: Request, sort: str = catalog.DEFAULT_SORT):
    sort = catalog.normalise_sort(sort)
    return _page(request, "index.html", books=catalog.browse(limit=12, sort=sort),
                 cover_url=catalog.cover_url, sort=sort,
                 sort_options=catalog.SORT_OPTIONS)


@router.get("/books", response_class=HTMLResponse)
async def book_list(request: Request, sort: str = catalog.DEFAULT_SORT):
    sort = catalog.normalise_sort(sort)
    return _page(request, "index.html", books=catalog.browse(sort=sort),
                 cover_url=catalog.cover_url, sort=sort,
                 sort_options=catalog.SORT_OPTIONS)


@router.get("/search", response_class=HTMLResponse)
async def search(request: Request, q: str = ""):
    results = catalog.browse(search=q) if q else []
    return _page(request, "search.html", books=results, query=q,
                 cover_url=catalog.cover_url)


@router.get("/books/{slug}", response_class=HTMLResponse)
async def book_detail(request: Request, slug: str):
    book = catalog.get_by_slug(slug)
    if not book:
        return _page(request, "not_found.html", thing="book")
    return _page(request, "book_detail.html", book=book, cover_url=catalog.cover_url)


# ── Basket ──────────────────────────────────────────────────────────────────

@router.get("/cart", response_class=HTMLResponse)
async def view_cart(request: Request):
    customer, cart = _viewer(request)
    country = customer.country_code if customer else "US"
    quote = checkout.quote_cart(cart, customer, country) if not cart.is_empty else None
    return _page(request, "cart.html", quote=quote)


@router.post("/cart/add")
async def add_to_cart(request: Request):
    values = await form_data(request)
    customer, _ = _viewer(request)
    edition_id = as_int(values, "edition_id")
    quantity = max(1, as_int(values, "quantity", 1))

    try:
        cookie = checkout.add_to_cart(
            customer, request.cookies.get(guest_cart.COOKIE_NAME), edition_id, quantity)
    except checkout.CheckoutError:
        return RedirectResponse("/cart", status_code=303)

    response = RedirectResponse("/cart", status_code=303)
    if cookie is not None:
        response.set_cookie(guest_cart.COOKIE_NAME, cookie, httponly=True, samesite="lax")
    return response


@router.post("/cart/remove")
async def remove_from_cart(request: Request):
    values = await form_data(request)
    customer, _ = _viewer(request)
    cookie = checkout.remove_from_cart(
        customer, request.cookies.get(guest_cart.COOKIE_NAME), as_int(values, "edition_id"))

    response = RedirectResponse("/cart", status_code=303)
    if cookie is not None:
        response.set_cookie(guest_cart.COOKIE_NAME, cookie, httponly=True, samesite="lax")
    return response


# ── Checkout ────────────────────────────────────────────────────────────────

@router.get("/checkout", response_class=HTMLResponse)
async def checkout_page(request: Request):
    customer, cart = _viewer(request)
    if cart.is_empty:
        return RedirectResponse("/cart", status_code=303)
    country = customer.country_code if customer else "US"
    return _page(request, "checkout.html",
                 quote=checkout.quote_cart(cart, customer, country), country=country)


@router.post("/checkout")
async def submit_checkout(request: Request):
    values = await form_data(request)
    customer, cart = _viewer(request)
    email = values.get("email") or (customer.email if customer else "")
    country = (values.get("country") or (customer.country_code if customer else "US")).upper()

    try:
        order = checkout.place_order(cart, customer, email, country)
    except checkout.CheckoutError as exc:
        quote = checkout.quote_cart(cart, customer, country) if not cart.is_empty else None
        return _page(request, "checkout.html", quote=quote, country=country, error=str(exc))

    response = RedirectResponse(f"/orders/{order['order_number']}", status_code=303)
    response.delete_cookie(guest_cart.COOKIE_NAME)
    return response


@router.get("/orders/{order_number}", response_class=HTMLResponse)
async def order_confirmation(request: Request, order_number: str):
    order = orders.get_by_number(order_number)
    if not order:
        return _page(request, "not_found.html", thing="order")
    return _page(request, "order_confirmation.html", order=order,
                 items=orders.items(order["id"]),
                 downloads=fulfillment.downloads_for_order(order["id"]),
                 shipments=fulfillment.shipments_for_order(order["id"]))


# ── Account ─────────────────────────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return _page(request, "login.html", accounts=identity.list_customers())


@router.post("/login")
async def login(request: Request):
    values = await form_data(request)
    customer = identity.authenticate(values.get("email", ""), values.get("password", ""))
    if not customer:
        return _page(request, "login.html", accounts=identity.list_customers(),
                     error="Those details did not match an account.")

    session_id = identity.start_session(customer.id)
    response = RedirectResponse("/account", status_code=303)
    response.set_cookie(SESSION_COOKIE, session_id, httponly=True, samesite="lax")
    return response


@router.post("/logout")
async def logout(request: Request):
    session_id = request.cookies.get(SESSION_COOKIE)
    if session_id:
        identity.end_session(session_id)
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie(SESSION_COOKIE)
    return response


@router.get("/account", response_class=HTMLResponse)
async def account(request: Request):
    customer, _ = _viewer(request)
    if not customer:
        return RedirectResponse("/login", status_code=303)
    return _page(request, "account.html", orders=orders.history(customer.id),
                 legacy=identity.is_legacy_account(customer))
