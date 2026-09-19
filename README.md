# LocalBooks

A second-hand bookshop that sells physical and digital editions. Browse the
catalogue, add to a basket, check out as a guest or as an account holder, and
watch the order move through payment and fulfilment.

## Requirements

Python 3.10 or newer. Nothing else — no database server, no message broker, no
accounts with any third party.

## Running it

```bash
pip install -r requirements.txt
python -m tools.cli seed
uvicorn main:app --reload
```

Then open <http://localhost:8000>. The staff console is at `/admin`.

Every demo account uses the password `demo`; the sign-in page lists them.

## Command line

```bash
python -m tools.cli seed        # load the catalogue, accounts and order history
python -m tools.cli status      # summarise what is in the database
python -m tools.cli reconcile   # queue the nightly stock check
python -m tools.cli fulfil      # process queued work
```

Starting over is just `rm bookstore.db` followed by `seed`.

## Placing a test order

Add something to your basket and check out. The order will sit unpaid until the
payment provider confirms it — open it under `/admin/orders/...` and press
**Confirm payment** to simulate that, then **Run fulfilment now** to process it.

Nothing is actually emailed. Every message the shop produces is recorded and
visible at `/admin/outbox`.

## Configuration

Everything works unconfigured. Set these to talk to the real services instead of
the built-in stand-ins:

| Variable | Effect |
|---|---|
| `DATABASE_URL` | Defaults to a local SQLite file |
| `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET` | Live payments and webhook verification |
| `SENDGRID_API_KEY` | Actually send email |
| `S3_BUCKET`, `S3_ENDPOINT` | Serve covers and ebook files from object storage |
| `FEATURE_NEW_CHECKOUT` | Switch to the rewritten checkout |
| `SESSION_SECRET` | Change this anywhere real |

`docker-compose.yml` describes how this runs in production. Local development
needs none of it.

## The books

Twenty public-domain titles. Covers are generated; three titles ship a real
downloadable PDF.
