"""Domain models shared across services.

These are the shapes that cross module boundaries. Repositories return dicts
straight from SQLite; services wrap them in these models before handing them on.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class EditionFormat(str, Enum):
    HARDCOVER = "hardcover"
    PAPERBACK = "paperback"
    EBOOK = "ebook"

    @property
    def is_digital(self) -> bool:
        return self is EditionFormat.EBOOK


class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class FulfillmentStatus(str, Enum):
    PENDING = "pending"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    DOWNLOADABLE = "downloadable"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class PricingScheme(str, Enum):
    STANDARD = "standard"
    LEGACY = "legacy"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class Edition(BaseModel):
    id: int
    book_id: int
    format: EditionFormat
    price_cents: int
    currency: str = "USD"
    isbn: Optional[str] = None
    asset_path: Optional[str] = None
    on_hand: Optional[int] = None

    @property
    def in_stock(self) -> bool:
        if self.format.is_digital:
            return True
        return (self.on_hand or 0) > 0


class Book(BaseModel):
    id: int
    slug: str
    title: str
    author: str
    description: str = ""
    published_year: Optional[int] = None
    cover_path: Optional[str] = None
    editions: list[Edition] = []

    @property
    def price_from_cents(self) -> Optional[int]:
        prices = [e.price_cents for e in self.editions]
        return min(prices) if prices else None


class BestSeller(BaseModel):
    """A book with how many copies of it have sold."""

    book: Book
    copies_sold: int


class CartLine(BaseModel):
    edition_id: int
    quantity: int
    unit_price_cents: int
    title: str = ""
    author: str = ""
    format: Optional[EditionFormat] = None
    slug: str = ""

    @property
    def line_total_cents(self) -> int:
        return self.unit_price_cents * self.quantity


class Cart(BaseModel):
    lines: list[CartLine] = []
    customer_id: Optional[int] = None

    @property
    def subtotal_cents(self) -> int:
        return sum(line.line_total_cents for line in self.lines)

    @property
    def item_count(self) -> int:
        return sum(line.quantity for line in self.lines)

    @property
    def is_empty(self) -> bool:
        return not self.lines

    @property
    def has_physical_items(self) -> bool:
        return any(l.format and not l.format.is_digital for l in self.lines)


class Customer(BaseModel):
    id: int
    email: str
    name: str
    country_code: str = "US"
    created_at: datetime


class PriceBreakdown(BaseModel):
    """What the customer is charged, and which rules produced it."""

    subtotal_cents: int
    discount_cents: int = 0
    tax_cents: int = 0
    total_cents: int
    pricing_scheme: PricingScheme = PricingScheme.STANDARD
    tax_label: Optional[str] = None
    notes: list[str] = []
