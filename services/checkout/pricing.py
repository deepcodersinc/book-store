"""Price calculation.

Two pricing schemes run side by side. Accounts opened before the cutoff are
still on the original agreement, which discounts differently from the current
one; everyone else gets standard pricing. On top of that, EU orders carry VAT.
"""

import settings
from packages.schemas.models import Cart, Customer, PriceBreakdown, PricingScheme

STANDARD_BULK_THRESHOLD = 3
STANDARD_BULK_DISCOUNT = 0.10

LEGACY_FLAT_DISCOUNT = 0.15
LEGACY_FREE_SHIPPING_FLOOR_CENTS = 2500


def _standard_discount(cart: Cart) -> tuple[int, list[str]]:
    if cart.item_count < STANDARD_BULK_THRESHOLD:
        return 0, []
    discount = int(cart.subtotal_cents * STANDARD_BULK_DISCOUNT)
    return discount, [f"Bulk discount applied ({STANDARD_BULK_THRESHOLD}+ items)"]


def _legacy_discount(cart: Cart) -> tuple[int, list[str]]:
    """The original agreement: flat percentage off, no quantity threshold."""
    discount = int(cart.subtotal_cents * LEGACY_FLAT_DISCOUNT)
    notes = ["Legacy account pricing"]
    if cart.subtotal_cents >= LEGACY_FREE_SHIPPING_FLOOR_CENTS and cart.has_physical_items:
        notes.append("Free shipping (legacy agreement)")
    return discount, notes


def _vat(taxable_cents: int, country_code: str) -> tuple[int, str | None]:
    if country_code.upper() not in settings.EU_COUNTRIES:
        return 0, None
    return int(taxable_cents * settings.VAT_RATE), f"VAT {int(settings.VAT_RATE * 100)}%"


def quote(cart: Cart, customer: Customer | None, country_code: str) -> PriceBreakdown:
    """Work out what this cart costs, and record which rules produced it."""
    from services.identity import service as identity

    scheme = PricingScheme.STANDARD
    if customer is not None and identity.is_legacy_account(customer):
        scheme = PricingScheme.LEGACY

    if scheme is PricingScheme.LEGACY:
        discount, notes = _legacy_discount(cart)
    else:
        discount, notes = _standard_discount(cart)

    taxable = cart.subtotal_cents - discount
    tax, tax_label = _vat(taxable, country_code)
    if tax_label:
        notes.append(f"{tax_label} for {country_code.upper()}")

    return PriceBreakdown(
        subtotal_cents=cart.subtotal_cents,
        discount_cents=discount,
        tax_cents=tax,
        total_cents=taxable + tax,
        pricing_scheme=scheme,
        tax_label=tax_label,
        notes=notes,
    )
