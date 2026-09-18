"""Order lifecycle.

Orders record which pricing scheme and which checkout implementation produced
them, so it is always possible to tell after the fact which path a purchase took.
"""

from data import orders as order_repo
from packages.schemas.models import Cart, Customer, OrderStatus, PriceBreakdown
from services.notifications import service as notifications


def create(cart: Cart, customer: Customer | None, email: str, country_code: str,
           breakdown: PriceBreakdown, version: str) -> dict:
    order_number = order_repo.next_order_number()
    order_id = order_repo.create_order(
        order_number=order_number,
        customer_id=customer.id if customer else None,
        email=email,
        subtotal_cents=breakdown.subtotal_cents,
        discount_cents=breakdown.discount_cents,
        tax_cents=breakdown.tax_cents,
        total_cents=breakdown.total_cents,
        country_code=country_code,
        pricing_scheme=breakdown.pricing_scheme.value,
        checkout_version=version,
    )
    for line in cart.lines:
        order_repo.add_order_item(
            order_id, line.edition_id, line.quantity, line.unit_price_cents,
            line.format.value if line.format else "paperback",
        )
    return order_repo.get_order(order_id)


def get(order_id: int) -> dict | None:
    return order_repo.get_order(order_id)


def get_by_number(order_number: str) -> dict | None:
    return order_repo.get_by_number(order_number)


def items(order_id: int) -> list[dict]:
    return order_repo.items_for_order(order_id)


def history(customer_id: int) -> list[dict]:
    return order_repo.list_orders(customer_id=customer_id)


def recent(limit: int = 50) -> list[dict]:
    return order_repo.list_orders(limit=limit)


def mark_paid(order_id: int) -> None:
    """Payment cleared. Confirm to the customer and hand off to fulfilment."""
    from services.fulfillment import service as fulfillment

    order = order_repo.get_order(order_id)
    if not order or order["status"] != OrderStatus.PENDING.value:
        return

    order_repo.set_status(order_id, OrderStatus.PAID.value)
    notifications.order_confirmed(order, order_repo.items_for_order(order_id))
    fulfillment.schedule(order_id)


def mark_fulfilled(order_id: int) -> None:
    order_repo.set_status(order_id, OrderStatus.FULFILLED.value)


def mark_refunded(order_id: int) -> None:
    order_repo.set_status(order_id, OrderStatus.REFUNDED.value)
