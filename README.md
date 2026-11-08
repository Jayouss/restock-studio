# Restock Studio ↗

A production-grade, highly resilient back-in-stock notification system, embeddable customer signup widget, and administrative operations dashboard. Built as a self-contained, zero-external-dependency Python service for the [Back-in-Stock build challenge](https://github.com/yitzi-farla/back-in-stock-challenge/blob/master/BRIEF.md).

**Stack:** Python 3.12 standard library, SQLite WAL, vanilla JS/CSS. **Zero pip dependencies.**

---

## Live Production Deployment

- **Live Production URL:** [https://restock.jayous-research.web.id](https://restock.jayous-research.web.id)
- **Customer Embed Widget:** [https://restock.jayous-research.web.id/embed](https://restock.jayous-research.web.id/embed)
- **Admin Dashboard:** [https://restock.jayous-research.web.id/admin](https://restock.jayous-research.web.id/admin)
- **Health Check Probe:** [https://restock.jayous-research.web.id/healthz](https://restock.jayous-research.web.id/healthz)
- **Direct VPS Failover URL:** [https://algovia.duckdns.org](https://algovia.duckdns.org)

---

## Core Capabilities & Architecture

- `GET /` — Responsive system overview, active routes, and embed instructions.
- `GET /embed` — Mobile-ready, iframe-embeddable customer subscription widget with SKU auto-population (`/embed?sku=TEE-ORG-WHT-M`), client validation, accessible ARIA attributes, and feedback states.
- `POST /api/requests` — Atomic customer subscription endpoint with email normalization, SKU validation, and ACID deduplication (`201 Created` for new requests, `200 OK` for existing active subscriptions).
- `POST /webhooks/stock` — Inventory webhook receiver protected by constant-time `X-Webhook-Secret` verification. Deduplicates incoming `event_id` keys idempotently with `202 Accepted`.
- **Authoritative Inventory Verification:** Webhook quantities are strictly treated as advisory hints. Restock alerts are dispatched **only** after authoritative confirmation via `GET STOCK_API_URL/{sku}` (`quantity > 0` and `in_stock != false`). Phantom restocks are safely filtered with 0 emails triggered.
- **Transactional Outbox & Idempotency:** SQLite transactions, lease timeouts, exponential backoff, and stable per-alert `Idempotency-Key` headers guarantee resilient delivery across network drops, timeouts, and simulated HTTP 500 provider outages without duplicate email delivery.
- **Continuous Reconciliation:** Background worker periodically polls open subscriptions against the authoritative stock API, catching stock updates that occurred during network interruptions or outbox recovery.
- `GET /admin` & `POST /admin/login` — Operations dashboard displaying subscription volume, delivery logs, retry attempts, and outbox leases. Protected by HMAC-SHA256 authenticated session cookies.
- **Security Hardening:** Strict Content Security Policy (`CSP`), HSTS, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, non-root execution inside Docker (`restock` UID 1000), and timing-attack-resistant constant-time secret comparison.
- `GET /healthz` & `HEAD /healthz` — Lightweight health check endpoint for container platforms, reverse proxies, and uptime monitors.

---

## Route Specification

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| `GET`, `HEAD` | `/healthz` | Public | Returns `200 ok` for health probes |
| `GET` | `/` | Public | Homepage, documentation, and live preview |
| `GET` | `/embed` | Public | Customer signup form (supports `?sku=...`) |
| `POST` | `/api/requests` | Public | Subscribes email to SKU (`201` or `200`) |
| `POST` | `/webhooks/stock` | `X-Webhook-Secret` | Ingests inventory events (`202 Accepted`) |
| `GET`, `POST` | `/admin/login` | Form / Password | Admin authentication with signed cookie |
| `GET` | `/admin` | Session Cookie | Operations dashboard & delivery log |
| `POST` | `/admin/logout` | Session Cookie | Clears admin session |
| `GET` | `/static/*` | Public | Static assets (CSS, embed JS) |

---

## Production Deployment Architecture

```
[Internet]
    │
    ▼
[Nginx Reverse Proxy (Port 443 TLS)]
    │ proxy_pass http://127.0.0.1:8000
    ▼
[Docker Container: restock-studio (Non-root user UID 1000)]
    │
    ├── App Process (Python 3.12 BaseHTTPHandler)
    │     ├── Webhook & API Handlers
    │     ├── Background Outbox Worker
    │     └── Periodic Stock Reconciler
    │
    └── Persistent Host Mount: /app/data
          └── restock.sqlite3 (WAL mode, ACID durability)
    │
[Host Cron Service]
    └── Daily Online SQLite Backup (scripts/backup.py, 7-day retention)
```

---

## Running with Docker Compose

1. Copy `.env.example` to `.env` and configure your credentials:
   ```bash
   cp .env.example .env
   ```

2. Start the service with Docker Compose:
   ```bash
   docker compose up -d --build
   ```

3. Verify container health:
   ```bash
   docker compose ps
   docker compose logs -f
   ```

Persistent data is stored in the host directory `./data` (mounted to `/app/data` inside the container), ensuring zero data loss across container rebuilds or updates.

---

## Automated Backups

Consistent, zero-downtime SQLite backups are managed by `scripts/backup.py` using SQLite's online backup API:

```bash
# Manual backup execution
python3 scripts/backup.py

# Automated daily cron schedule (e.g., at 02:00 UTC)
0 2 * * * /usr/bin/python3 /path/to/restock-studio/scripts/backup.py >> /path/to/restock-studio/backups/backup.log 2>&1
```

Backups are timestamped and automatically pruned after 7 days.

---

## Local Development (No Docker Required)

Requires Python 3.11+.

```bash
# Set environment variables from .env
set -a; source .env; set +a

# Start the application
python app.py
```

On Windows PowerShell:

```powershell
Get-Content .env | Where-Object { $_ -match '^[A-Z_]+=' } | ForEach-Object {
  $key, $value = $_ -split '=', 2
  [Environment]::SetEnvironmentVariable($key, $value.Trim('"'))
}
python app.py
```

---

## Automated Integration Tests

Run the full end-to-end integration test suite (8 tests covering concurrency, deduplication, phantom webhooks, provider 500 retry backoff with idempotency, and SQLite restart survival):

```bash
# Run from repository root
python -m unittest discover -s tests -v
```

CI is configured via GitHub Actions (`.github/workflows/ci.yml`), running integration tests and validating container builds on every commit.

---

## Verification Against Official Test Harness

The production deployment has been verified against the official challenge harness (`https://harness-production-e601.up.railway.app`):

1. **Customer Subscriptions:** Verified `POST /api/requests` with valid emails and SKUs returned HTTP 201.
2. **Duplicate Protection:** Resubmission of the identical email and SKU returned HTTP 200 without creating duplicate alert records.
3. **Webhook Security:** Unauthorized webhooks without `X-Webhook-Secret` or with an invalid secret were rejected with HTTP 401.
4. **Duplicate Webhook Deduplication:** Delivery of duplicate event IDs returned HTTP 202 without duplicate email outbox jobs.
5. **Phantom Restock:** Webhook reporting 14 items for a product with 0 actual stock in the authoritative stock API was safely verified; 0 emails were dispatched.
6. **Injected Provider 500 Outage:** Simulated HTTP 500 on mock Resend provider was safely caught; outbox retried using an identical `Idempotency-Key` and was accepted with exactly 1 email received.
7. **Autonomous Simulation:** Successfully passed live multi-turn store simulation ticks.
