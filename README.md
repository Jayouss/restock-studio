# Restock Studio ↗

A polished, reliable back-in-stock signup widget, email notifications, and admin dashboard. Built as a self-contained Python application for the [Back-in-Stock build challenge](https://github.com/yitzi-farla/back-in-stock-challenge/blob/master/BRIEF.md).

**Stack:** Python 3.12 standard library, SQLite WAL, vanilla JS/CSS. **No pip dependencies.**

## Features

- `GET /embed` — responsive iframe-friendly product SKU + email form (`/embed?sku=TEE-ORG-WHT-M` pre-fills the SKU).
- `POST /api/requests` — validates `{ "email": "customer@example.com", "sku": "TEE-ORG-WHT-M" }` and atomically deduplicates active alerts; responds 201 (new) or 200 (duplicate).
- `POST /webhooks/stock` — authenticates using constant-time comparison against `X-Webhook-Secret`, stores each `event_id` once, and processes it asynchronously.
- **Authoritative verification:** a reported restock *never* triggers mail before `GET STOCK_API_URL/{sku}` confirms `quantity > 0` and `in_stock != false`. Periodic reconciliation also catches restocks missed during an outage or subscriptions created while the product is already available.
- **Durable outbox:** SQLite transactions, leases, retry with exponential backoff, and a stable `Idempotency-Key` per alert let the sender recover from crashes, timeouts, and injected HTTP 500s. Simultaneous duplicate webhooks never create duplicate active alerts or email jobs.
- `GET /admin` — login-protected, responsive operations dashboard with alert status and notified timestamps.
- **HTML email** — responsive, table-based, escaped dynamic fields, Resend API compatible.
- `/healthz` — simple health check for container platforms.

## Run locally

1. Sign up at the [test server](https://harness-production-e601.up.railway.app/) with invite code `stock-e11d21` and **bookmark your personal dashboard link**. Copy your sandbox keys; never commit them.
2. Copy `.env.example` to `.env` and fill the real values from your dashboard. Set the stock URL to `<harness-origin>/api/stock` and Resend base URL to `<harness-origin>` (no `/emails` suffix).
3. Export the variables, then run Python 3.11+:

```bash
# Linux / macOS (export values from .env using your preferred safe env loader)
set -a; source .env; set +a
python app.py
```

Visit `http://localhost:8000`, `http://localhost:8000/embed`, and `http://localhost:8000/admin`.

**Windows PowerShell** (after editing `.env`):

```powershell
Get-Content .env | Where-Object { $_ -match '^[A-Z_]+=' } | ForEach-Object {
  $key, $value = $_ -split '=', 2
  [Environment]::SetEnvironmentVariable($key, $value.Trim('"'))
}
python app.py
```

## Docker (required by challenge)

```bash
docker build -t restock-studio .
docker run --rm -p 8000:8000 --env-file .env -v restock_data:/app/data restock-studio
```

The service listens on `$PORT` (defaults to `8000`). The five challenge-provided credentials plus `$PORT` are enough to start. Set `ADMIN_PASSWORD` separately if possible; for exact compatibility with the mandatory env list the **fallback admin password is `WEBHOOK_SECRET`**. Do not reuse this secret in a real production system.

**Important storage detail:** SQLite survives process restarts because it writes to disk. Mount `/app/data` as a persistent volume to survive container replacement/redeploy. A host with an ephemeral filesystem **must** be given a persistent volume; otherwise no SQLite application can preserve records across redeploys. Run **one instance** unless all instances share a transaction-safe SQLite volume; for horizontally scaled production, use a managed relational database.

## Deploy and connect to the harness

Railway / Render / Fly / VPS are all suitable; deploy the Dockerfile, set the required variables and `PORT`, and attach a persistent disk at `/app/data`. Set `ADMIN_PASSWORD` in deployment secrets. If the host auto-provides `$PORT`, the app will use it automatically.

In your **personal harness dashboard**, paste the deployed app's public root URL (e.g. `https://YOUR-SERVICE.example`, without `/embed`), and start / resume its store simulation. The harness will POST customer requests to `/api/requests`, fire stock events at `/webhooks/stock`, and collect outgoing `/emails` into its inbox. The harness also has buttons to simulate a phantom restock, duplicate event, and email failure.

While developing locally you may instead tunnel `http://localhost:8000` using `cloudflared` or `ngrok`. The brief explicitly permits this.

## Example API calls

```bash
curl -i http://localhost:8000/api/requests \
  -H 'Content-Type: application/json' \
  -d '{"email":"customer@example.com","sku":"TEE-ORG-WHT-M"}'

curl -i http://localhost:8000/webhooks/stock \
  -H 'Content-Type: application/json' -H "X-Webhook-Secret: $WEBHOOK_SECRET" \
  -d '{"event_id":"evt-demo-1","sku":"TEE-ORG-WHT-M","quantity":8}'
```

Use the harness's **Set stock** control (not just a claimed webhook quantity) to mark an item truly in stock. Check the inbox after the email is accepted.

## Reliability design — how we avoid duplicate *and* missed emails

1. **Request uniqueness:** a partial unique index on `(email,sku)` when status is `open` or `queued`. The constraint is inside SQLite, so simultaneous incoming POSTs are safe.
2. **Webhook uniqueness:** `stock_events.event_id` is the primary key. New events are committed before returning `202`. Duplicate event IDs return `202` but do not enqueue twice.
3. **Stock verification:** webhook payloads are hints only. Authoritative stock is checked using the given Bearer token; on errors, events retry. A phantom restock does not notify.
4. **Outbox transaction:** switching requests to `queued` and inserting unique delivery records happens in one `BEGIN IMMEDIATE` transaction. A crash cannot lose a job in between.
5. **Send retry:** jobs are claimed with leases and retried on HTTP 500, timeouts, and ambiguous network failures. Attempts use an identical `Idempotency-Key` derived from the request ID. The harness/Resend deduplicates retries even if the first send succeeded but our response was lost.
6. **Recovery and reconciliation:** in-progress leases expire; startup resumes the outbox. A periodic per-SKU stock check compensates for missed webhook delivery or temporary upstream errors. Successfully sent jobs can never send again.

**Email delivery caveat:** no application can guarantee absolute exactly-once effects across a network without a cooperating provider. This project uses the mock Resend service's supported idempotency keys to achieve effectively-once email acceptance for retries.

## Environment variables

| Variable | Required | Description |
| --- | --- | --- |
| `STOCK_API_URL` | Yes | `https://harness-production-e601.up.railway.app/api/stock` |
| `STOCK_API_KEY` | Yes | Bearer token for the stock endpoint |
| `RESEND_API_KEY` | Yes | Bearer token for mock Resend |
| `RESEND_BASE_URL` | Yes | `https://harness-production-e601.up.railway.app` |
| `WEBHOOK_SECRET` | Yes | Validates `X-Webhook-Secret` |
| `PORT` | Platform-provided | Listening port, default 8000 |
| `ADMIN_PASSWORD` | Recommended | Dashboard password; defaults to webhook secret for challenge compatibility |
| `DB_PATH` | No | SQLite file, defaults to `/app/data/restock.sqlite3` in Docker |
| `RECONCILE_SECONDS` | No | Re-check open SKUs every 20 seconds |
| `POLL_SECONDS` | No | Worker polling interval (default 0.5 seconds) |
| `FROM_EMAIL` | No | Default test sender. Real Resend requires a verified sender domain. |
| `SHOP_URL` | No | Optional product/store link in email; only HTTP(S) links are rendered |

## Automated tests

Run with no extra dependencies:

```bash
python -m unittest discover -s tests -v
```

Tests simulate a stock API and Resend server (including 500 failures, retry idempotency, unauthorized webhooks, duplicate subscription requests, phantom stock, and persistent SQLite state). **Passing local tests is not a substitute for verifying your own credentials against the live challenge harness.**

## Submission checklist

- [ ] Run automated tests locally.
- [ ] Create a new GitHub repository and push these project files (not `.env`).
- [ ] Deploy the Dockerfile with a persistent volume and secrets.
- [ ] Register the app's root URL in your harness candidate dashboard; check its inbox, duplicate webhook handling, retry behavior, and admin login.
- [ ] Include GitHub URL, live app URL, AI tools used, and **your actual** elapsed completion time in your Upwork proposal.
