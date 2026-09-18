"""Operations CLI.

    python -m tools.cli seed        load the catalogue and demo accounts
    python -m tools.cli fulfil      drain the fulfilment queue
    python -m tools.cli reconcile   queue the nightly stock reconciliation
    python -m tools.cli status      summarise what is in the database
"""

import sys

from data import db
from services.catalog import service as catalog
from services.fulfillment import service as fulfillment
from services.inventory import service as inventory
from services.orders import service as orders
from tools.cli import seeder
from workers.fulfillment import worker


def cmd_seed() -> int:
    db.init_schema()
    if catalog.catalogue_size() > 0:
        print("Catalogue already populated. Delete bookstore.db to start over.")
        return 0
    summary = seeder.run()
    print(f"Seeded {summary['books']} books, {summary['editions']} editions, "
          f"{summary['customers']} customers, {summary['orders']} orders.")
    return 0


def cmd_fulfil() -> int:
    db.init_schema()
    if "--loop" in sys.argv:
        return _fulfil_forever()
    processed = worker.drain()
    if not processed:
        print("Nothing queued.")
        return 0
    for outcome in processed:
        print(f"  job {outcome['job_id']} [{outcome['type']}] -> {outcome['status']}")
    print(f"Processed {len(processed)} job(s).")
    return 0


def _fulfil_forever(interval: float = 5.0) -> int:
    """Long-running mode, as the worker container runs it."""
    import time

    print(f"Draining the queue every {interval:g}s. Ctrl-C to stop.")
    try:
        while True:
            for outcome in worker.drain():
                print(f"  job {outcome['job_id']} [{outcome['type']}] -> {outcome['status']}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


def cmd_reconcile() -> int:
    db.init_schema()
    job_id = fulfillment.schedule_reconciliation()
    print(f"Queued reconciliation job {job_id}. Run 'fulfil' to process it.")
    return 0


def cmd_status() -> int:
    db.init_schema()
    low = inventory.needs_reordering()
    print(f"Books:        {catalog.catalogue_size()}")
    print(f"Orders:       {len(orders.recent(limit=1000))}")
    print(f"Queued jobs:  {len(fulfillment.pending())}")
    print(f"Low stock:    {len(low)}")
    for row in low:
        print(f"  - {row['title']} ({row['format']}): {row['on_hand']} left")
    return 0


COMMANDS = {
    "seed": cmd_seed,
    "fulfil": cmd_fulfil,
    "fulfill": cmd_fulfil,
    "reconcile": cmd_reconcile,
    "status": cmd_status,
}


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] not in COMMANDS:
        print(__doc__)
        return 1
    return COMMANDS[argv[1]]()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
