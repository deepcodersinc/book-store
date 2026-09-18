# Marginalia Books

A second-hand bookshop that sells physical and digital editions. Browse the
catalogue, add to a basket, check out as a guest or as an account holder, and
watch the order move through payment and fulfilment.

## Running it

Two commands, no infrastructure:

```bash
pip install -r requirements.txt
python -m tools.cli seed
uvicorn main:app --reload
```

Then open <http://localhost:8000>. Staff console is at `/admin`.

Every demo account uses the password `demo` — the sign-in page lists them.

## How it fits together

```
apps/storefront      shopper-facing pages
apps/admin           staff console
apps/api             public endpoints: partner feed, Stripe webhook, downloads
services/            business logic, one package per capability
data/                SQLite repositories
integrations/        Stripe, SendGrid, object storage
workers/fulfillment  drains the job queue
packages/            shared models and web helpers
tools/cli            seed, fulfil, reconcile, status
```

**The catalogue is reached through `services/catalog`, never directly.** Pages ask
services for what they need; only `data/` knows SQL. Keeping that line intact is
what stops the storefront from growing its own queries.

## Things that branch

The shop has accumulated the usual exceptions, and they are all live:

| Branch | Condition |
|---|---|
| Guest vs account basket | Signed-out shoppers keep the basket in a signed cookie; account holders get a row in `carts` |
| Legacy pricing | Accounts opened before 2019 are still on a flat 15% agreement instead of the current bulk discount |
| VAT | Orders shipping to an EU country are taxed at 20% |
| Checkout v1 / v2 | `FEATURE_NEW_CHECKOUT=true` switches to the rewrite, which checks stock *before* charging |
| Digital vs physical | Ebooks get a time-limited download link; physical stock is decremented and shipped |
| Refunds | Digital refunds settle immediately; physical ones wait for the book to come back |

Every order records which of these applied — see `pricing_scheme` and
`checkout_version` on the orders table, and `format` on each line.

## Driving a full order by hand

```bash
python -m tools.cli seed        # catalogue, accounts, order history
python -m tools.cli status      # what is in the database
python -m tools.cli reconcile   # queue the nightly stock check
python -m tools.cli fulfil      # drain the queue
```

Place an order in the browser, then open the order in `/admin/orders/...` and hit
**Confirm payment** — that replays the webhook Stripe would post. Run
`python -m tools.cli fulfil` and the order ships or the download link appears.

Nothing is emailed. Every message the system produces is recorded and visible at
`/admin/outbox`.

## Configuration

Everything works unconfigured. Set these to talk to the real services:

| Variable | Effect |
|---|---|
| `DATABASE_URL` | Defaults to a local SQLite file |
| `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET` | Live payments and webhook verification |
| `SENDGRID_API_KEY` | Actually send email |
| `S3_BUCKET`, `S3_ENDPOINT` | Serve covers and ebooks from object storage |
| `FEATURE_NEW_CHECKOUT` | Switch to the rewritten checkout |

`docker-compose.yml` describes the production-like topology — Postgres, Redis,
MinIO and a separate worker. Local development needs none of it.

## Public endpoints

Reachable without a session:

- `GET /api/v1/books` — published catalogue feed. Partners read this, so the
  response shape is a contract.
- `POST /webhooks/stripe` — payment confirmations, verified by signature.
- `GET /download/{token}` — a purchased ebook, gated by a one-off expiring token.

## The books

Twenty public-domain titles. Covers are generated; three titles ship a real
downloadable PDF so the digital path has something to deliver.
