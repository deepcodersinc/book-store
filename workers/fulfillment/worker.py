"""Fulfilment worker.

Drains the job queue. What happens to a line depends entirely on its format:
a digital edition gets a time-limited download grant, a physical one gets picked,
shipped and tracked. Nothing else in the system branches this hard.
"""

import secrets
from datetime import datetime, timedelta

import settings
from data import fulfillment as fulfillment_repo
from packages.schemas.models import EditionFormat, FulfillmentStatus
from services.fulfillment.service import JOB_FULFIL_ORDER, JOB_RECONCILE_INVENTORY
from services.inventory import service as inventory
from services.notifications import service as notifications
from services.orders import service as orders


def _fulfil_digital(order: dict, item: dict) -> None:
    token = secrets.token_urlsafe(16)
    expires = datetime.utcnow() + timedelta(hours=settings.DOWNLOAD_EXPIRY_HOURS)
    fulfillment_repo.create_download(
        order_item_id=item["id"],
        token=token,
        expires_at=expires.isoformat(" ", "seconds"),
        max_downloads=settings.MAX_DOWNLOADS_PER_PURCHASE,
    )
    orders_repo_status = FulfillmentStatus.DOWNLOADABLE.value
    from data import orders as order_repo
    order_repo.set_item_fulfillment(item["id"], orders_repo_status)
    notifications.download_ready(order, item["title"], token)


def _fulfil_physical(order: dict, items: list[dict]) -> None:
    tracking = f"DP{secrets.randbelow(10**9):09d}"
    fulfillment_repo.create_shipment(order["id"], tracking)
    from data import orders as order_repo
    for item in items:
        order_repo.set_item_fulfillment(item["id"], FulfillmentStatus.SHIPPED.value)
    notifications.shipment_dispatched(order, tracking)


def fulfil_order(order_id: int) -> dict:
    order = orders.get(order_id)
    if not order:
        raise ValueError(f"No such order: {order_id}")

    items = orders.items(order_id)
    physical = []
    for item in items:
        if EditionFormat(item["format"]).is_digital:
            _fulfil_digital(order, item)
        else:
            physical.append(item)

    if physical:
        _fulfil_physical(order, physical)

    orders.mark_fulfilled(order_id)
    return {"order_id": order_id, "digital": len(items) - len(physical),
            "physical": len(physical)}


def reconcile_inventory() -> dict:
    report = inventory.reconcile()
    if report["titles"]:
        notifications.low_stock_alert(report["titles"])
    return report


def run_once() -> dict | None:
    """Process a single queued job. Returns None when the queue is empty."""
    job = fulfillment_repo.claim_next()
    if job is None:
        return None

    try:
        if job["type"] == JOB_FULFIL_ORDER:
            result = fulfil_order(job["payload"]["order_id"])
        elif job["type"] == JOB_RECONCILE_INVENTORY:
            result = reconcile_inventory()
        else:
            raise ValueError(f"Unknown job type: {job['type']}")
    except Exception as exc:  # noqa: BLE001 - the queue records every failure
        fulfillment_repo.fail(job["id"], str(exc))
        return {"job_id": job["id"], "type": job["type"], "status": "failed",
                "error": str(exc)}

    fulfillment_repo.complete(job["id"])
    return {"job_id": job["id"], "type": job["type"], "status": "done", "result": result}


def drain(limit: int = 100) -> list[dict]:
    """Work through the queue until it is empty."""
    processed = []
    for _ in range(limit):
        outcome = run_once()
        if outcome is None:
            break
        processed.append(outcome)
    return processed
