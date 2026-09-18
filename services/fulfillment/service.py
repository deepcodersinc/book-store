"""Fulfilment scheduling.

The order side of the queue: work is enqueued here and drained by the worker.
"""

from data import fulfillment as fulfillment_repo

JOB_FULFIL_ORDER = "fulfil_order"
JOB_RECONCILE_INVENTORY = "reconcile_inventory"


def schedule(order_id: int) -> int:
    """Queue an order for fulfilment once its payment has settled."""
    return fulfillment_repo.enqueue(JOB_FULFIL_ORDER, {"order_id": order_id})


def schedule_reconciliation() -> int:
    return fulfillment_repo.enqueue(JOB_RECONCILE_INVENTORY, {})


def pending() -> list[dict]:
    return fulfillment_repo.pending_jobs()


def recent(limit: int = 50) -> list[dict]:
    return fulfillment_repo.all_jobs(limit)


def downloads_for_order(order_id: int) -> list[dict]:
    return fulfillment_repo.downloads_for_order(order_id)


def get_download_grant(token: str) -> dict | None:
    """Resolve a download token to the grant and the file behind it."""
    return fulfillment_repo.get_download(token)


def record_download(download_id: int) -> None:
    fulfillment_repo.record_download(download_id)


def shipments_for_order(order_id: int) -> list[dict]:
    return fulfillment_repo.shipments_for_order(order_id)
