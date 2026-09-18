"""Cart handling and checkout orchestration.

Two things branch here. A shopper who is signed in gets a persisted cart; a
guest gets a cookie. And the checkout itself has two implementations — the
original one and a rewrite behind FEATURE_NEW_CHECKOUT — which differ in when
stock is reserved relative to taking payment.
"""

import settings
from data import carts as cart_repo
from packages.schemas.models import Cart, CartLine, Customer, EditionFormat, PriceBreakdown
from services.catalog import service as catalog
from services.checkout import guest_cart, pricing
from services.inventory import service as inventory
from services.orders import service as orders
from services.payments import service as payments


class CheckoutError(RuntimeError):
    pass


# ── Cart ────────────────────────────────────────────────────────────────────

def _line_from_edition(edition: dict, quantity: int, unit_price_cents: int) -> CartLine:
    return CartLine(
        edition_id=edition["id"],
        quantity=quantity,
        unit_price_cents=unit_price_cents,
        title=edition.get("title", ""),
        author=edition.get("author", ""),
        slug=edition.get("slug", ""),
        format=EditionFormat(edition["format"]),
    )


def load_cart(customer: Customer | None, cookie: str | None) -> Cart:
    if customer is None:
        lines = []
        for item in guest_cart.decode(cookie):
            edition = catalog.get_edition(item["edition_id"])
            if edition:
                lines.append(_line_from_edition(
                    edition, item["quantity"], item["unit_price_cents"]))
        return Cart(lines=lines)

    cart_id = cart_repo.get_or_create_cart(customer.id)
    lines = [
        CartLine(
            edition_id=row["edition_id"],
            quantity=row["quantity"],
            unit_price_cents=row["unit_price_cents"],
            title=row["title"],
            author=row["author"],
            slug=row["slug"],
            format=EditionFormat(row["format"]),
        )
        for row in cart_repo.lines_for_cart(cart_id)
    ]
    return Cart(lines=lines, customer_id=customer.id)


def add_to_cart(customer: Customer | None, cookie: str | None,
                edition_id: int, quantity: int = 1) -> str | None:
    """Add an item. Returns a new cookie value for guests, None for accounts."""
    edition = catalog.get_edition(edition_id)
    if not edition:
        raise CheckoutError("That edition does not exist")

    if customer is None:
        items = guest_cart.add(
            guest_cart.decode(cookie), edition_id, quantity, edition["price_cents"])
        return guest_cart.encode(items)

    cart_id = cart_repo.get_or_create_cart(customer.id)
    cart_repo.add_item(cart_id, edition_id, quantity, edition["price_cents"])
    return None


def remove_from_cart(customer: Customer | None, cookie: str | None,
                     edition_id: int) -> str | None:
    if customer is None:
        return guest_cart.encode(guest_cart.remove(guest_cart.decode(cookie), edition_id))
    cart_id = cart_repo.get_or_create_cart(customer.id)
    cart_repo.remove_item(cart_id, edition_id)
    return None


def quote_cart(cart: Cart, customer: Customer | None, country_code: str) -> PriceBreakdown:
    return pricing.quote(cart, customer, country_code)


# ── Checkout ────────────────────────────────────────────────────────────────

def place_order(cart: Cart, customer: Customer | None, email: str,
                country_code: str) -> dict:
    if cart.is_empty:
        raise CheckoutError("Your basket is empty")

    breakdown = pricing.quote(cart, customer, country_code)
    if settings.FEATURE_NEW_CHECKOUT:
        return _checkout_v2(cart, customer, email, country_code, breakdown)
    return _checkout_v1(cart, customer, email, country_code, breakdown)


def _checkout_v1(cart: Cart, customer: Customer | None, email: str,
                 country_code: str, breakdown: PriceBreakdown) -> dict:
    """Original flow: take the money first, then reserve stock."""
    order = orders.create(cart, customer, email, country_code, breakdown, version="v1")
    payments.charge(order["id"], breakdown.total_cents, order["order_number"])
    for line in cart.lines:
        if line.format and not line.format.is_digital:
            inventory.reserve(line.edition_id, line.quantity)
    _clear_cart(customer)
    return order


def _checkout_v2(cart: Cart, customer: Customer | None, email: str,
                 country_code: str, breakdown: PriceBreakdown) -> dict:
    """Rewrite: check stock before charging, so we never take money we can't fulfil."""
    for line in cart.lines:
        if line.format and not line.format.is_digital:
            if not inventory.can_fulfil(line.edition_id, line.quantity):
                raise CheckoutError(f"'{line.title}' is out of stock")

    order = orders.create(cart, customer, email, country_code, breakdown, version="v2")
    for line in cart.lines:
        if line.format and not line.format.is_digital:
            inventory.reserve(line.edition_id, line.quantity)
    payments.charge(order["id"], breakdown.total_cents, order["order_number"])
    _clear_cart(customer)
    return order


def _clear_cart(customer: Customer | None) -> None:
    if customer is None:
        return
    cart = cart_repo.get_active_cart(customer.id)
    if cart:
        cart_repo.mark_converted(cart["id"])
