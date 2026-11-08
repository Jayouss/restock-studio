"""Restock Studio — dependency-free, persistent back-in-stock alerts service.

Run with `python app.py` (Python 3.11+). Designed for the challenge's mock stock
and Resend endpoints; all external traffic is restricted to configured base URLs.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import html
import json
import logging
import os
import re
import secrets
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urlsplit
from urllib.request import Request, urlopen

import ui

LOG = logging.getLogger("restock")
ROOT = Path(__file__).resolve().parent
SKU_RE = re.compile(r"^[A-Z0-9][A-Z0-9._-]{0,63}$")
EMAIL_RE = re.compile(r"^[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+$")


class Config:
    def __init__(self, env=None):
        env = env if env is not None else os.environ
        self.port = int(env.get("PORT", "8000"))
        self.db_path = Path(env.get("DB_PATH", str(ROOT / "data" / "restock.sqlite3")))
        self.stock_url = env.get("STOCK_API_URL", "").rstrip("/")
        self.stock_key = env.get("STOCK_API_KEY", "")
        self.resend_url = env.get("RESEND_BASE_URL", "").rstrip("/")
        self.resend_key = env.get("RESEND_API_KEY", "")
        self.webhook_secret = env.get("WEBHOOK_SECRET", "")
        # The mandatory challenge env list does not include an admin password.
        # Default to the webhook secret; a separate ADMIN_PASSWORD is recommended.
        self.admin_password = env.get("ADMIN_PASSWORD") or self.webhook_secret
        self.from_email = env.get("FROM_EMAIL", "Restock Studio <alerts@restock.example>")
        self.shop_url = env.get("SHOP_URL", "")
        self.reconcile_seconds = max(1.0, float(env.get("RECONCILE_SECONDS", "20")))
        self.poll_seconds = max(0.1, float(env.get("POLL_SECONDS", "0.5")))


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def is_valid_email(address):
    return isinstance(address, str) and len(address) <= 254 and len(address) > 3 and EMAIL_RE.fullmatch(address) is not None


def normalize_sku(value):
    if not isinstance(value, str):
        return None
    sku = value.strip().upper()
    return sku if SKU_RE.fullmatch(sku) else None


class Store:
    """One SQLite connection per operation; transactions coordinate concurrent webhooks."""

    def __init__(self, path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.db() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS requests (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  email TEXT NOT NULL,
                  sku TEXT NOT NULL,
                  status TEXT NOT NULL DEFAULT 'open'
                    CHECK(status IN ('open','queued','notified')),
                  created_at TEXT NOT NULL,
                  notified_at TEXT,
                  provider_id TEXT
                );
                CREATE UNIQUE INDEX IF NOT EXISTS one_active_request
                  ON requests(email, sku) WHERE status IN ('open','queued');
                CREATE INDEX IF NOT EXISTS requests_by_sku ON requests(sku, status);
                CREATE TABLE IF NOT EXISTS stock_events (
                  event_id TEXT PRIMARY KEY,
                  sku TEXT NOT NULL,
                  quantity INTEGER NOT NULL,
                  status TEXT NOT NULL DEFAULT 'pending',
                  lease_until REAL DEFAULT 0,
                  next_attempt REAL DEFAULT 0,
                  attempts INTEGER NOT NULL DEFAULT 0,
                  created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS deliveries (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  request_id INTEGER NOT NULL UNIQUE REFERENCES requests(id),
                  status TEXT NOT NULL DEFAULT 'pending',
                  attempts INTEGER NOT NULL DEFAULT 0,
                  next_attempt REAL DEFAULT 0,
                  lease_until REAL DEFAULT 0,
                  idempotency_key TEXT NOT NULL UNIQUE,
                  provider_id TEXT,
                  last_error TEXT,
                  created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS deliveries_due
                  ON deliveries(status, next_attempt, lease_until);
            """)

    @contextmanager
    def db(self):
        conn = sqlite3.connect(self.path, timeout=20, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=20000")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self):
        with self.db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                yield conn
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise

    def add_request(self, email, sku):
        with self.transaction() as conn:
            inserted = conn.execute(
                "INSERT OR IGNORE INTO requests(email,sku,status,created_at) VALUES(?,?, 'open', ?)",
                (email, sku, utc_now()),
            ).rowcount == 1
            row = conn.execute(
                "SELECT id,status FROM requests WHERE email=? AND sku=? "
                "AND status IN ('open','queued') ORDER BY id DESC LIMIT 1",
                (email, sku),
            ).fetchone()
            row_dict = dict(row) if row else {"id": None, "status": "open"}
            return inserted, row_dict

    def add_event(self, event_id, sku, quantity):
        with self.transaction() as conn:
            return conn.execute(
                "INSERT OR IGNORE INTO stock_events(event_id,sku,quantity,created_at) VALUES(?,?,?,?)",
                (event_id, sku, quantity, utc_now()),
            ).rowcount == 1

    def claim_event(self):
        now = time.time()
        with self.transaction() as conn:
            row = conn.execute(
                "SELECT * FROM stock_events WHERE "
                "(status='pending' AND next_attempt<=?) OR "
                "(status='processing' AND lease_until<=?) "
                "ORDER BY created_at, event_id LIMIT 1", (now, now),
            ).fetchone()
            if row:
                conn.execute("UPDATE stock_events SET status='processing', lease_until=?, "
                             "attempts=attempts+1 WHERE event_id=?", (now + 15, row['event_id']))
            return dict(row) if row else None

    def finish_event(self, event_id, error=None, attempts=1):
        with self.transaction() as conn:
            if error:
                delay = min(60, 2 ** min(attempts, 6))
                conn.execute("UPDATE stock_events SET status='pending', next_attempt=?, lease_until=0 "
                             "WHERE event_id=?", (time.time() + delay, event_id))
            else:
                conn.execute("UPDATE stock_events SET status='done', lease_until=0 "
                             "WHERE event_id=?", (event_id,))

    def queue_sku(self, sku):
        """Atomic state transition: all open requests for SKU become durable outbox jobs."""
        with self.transaction() as conn:
            rows = conn.execute("SELECT id FROM requests WHERE sku=? AND status='open'", (sku,)).fetchall()
            count = 0
            for row in rows:
                request_id = row['id']
                key = f"stock-alert-request-{request_id}"
                conn.execute("INSERT OR IGNORE INTO deliveries(request_id,idempotency_key,created_at) "
                             "VALUES(?,?,?)", (request_id, key, utc_now()))
                count += conn.execute("UPDATE requests SET status='queued' WHERE id=? AND status='open'", (request_id,)).rowcount
            return count

    def claim_delivery(self):
        now = time.time()
        with self.transaction() as conn:
            row = conn.execute(
                "SELECT d.*,r.email,r.sku FROM deliveries d "
                "JOIN requests r ON r.id=d.request_id WHERE "
                "(d.status='pending' AND d.next_attempt<=?) OR "
                "(d.status='sending' AND d.lease_until<=?) "
                "ORDER BY d.next_attempt, d.id LIMIT 1", (now, now),
            ).fetchone()
            if row:
                conn.execute("UPDATE deliveries SET status='sending', lease_until=?, attempts=attempts+1 "
                             "WHERE id=?", (now + 15, row['id']))
            return dict(row) if row else None

    def finish_delivery(self, delivery_id, request_id, provider_id=None, error=None, attempts=1):
        with self.transaction() as conn:
            if error:
                delay = min(120, 2 ** min(attempts, 7))
                conn.execute("UPDATE deliveries SET status='pending', lease_until=0, "
                             "next_attempt=?, last_error=? WHERE id=?",
                             (time.time() + delay, str(error)[:300], delivery_id))
            else:
                conn.execute("UPDATE deliveries SET status='sent', lease_until=0, "
                             "provider_id=?, last_error=NULL WHERE id=?", (provider_id, delivery_id))
                conn.execute("UPDATE requests SET status='notified', notified_at=?,provider_id=? "
                             "WHERE id=? AND status='queued'", (utc_now(), provider_id, request_id))

    def open_skus(self):
        with self.db() as conn:
            return [r['sku'] for r in conn.execute(
                "SELECT DISTINCT sku FROM requests WHERE status='open' ORDER BY sku LIMIT 500"
            ).fetchall()]

    def dashboard(self, status="all"):
        with self.db() as conn:
            stats = {r['status']: r['n'] for r in conn.execute(
                "SELECT status, count(*) n FROM requests GROUP BY status"
            )}
            retrying = conn.execute("SELECT COUNT(*) FROM deliveries WHERE status!='sent' AND attempts>0").fetchone()[0]
            if status in ('open', 'queued', 'notified'):
                rows = conn.execute("SELECT r.*,d.attempts,d.last_error FROM requests r "
                                    "LEFT JOIN deliveries d ON d.request_id=r.id "
                                    "WHERE r.status=? ORDER BY r.id DESC LIMIT 150", (status,)).fetchall()
            else:
                rows = conn.execute("SELECT r.*,d.attempts,d.last_error FROM requests r "
                                    "LEFT JOIN deliveries d ON d.request_id=r.id "
                                    "ORDER BY r.id DESC LIMIT 150").fetchall()
            return stats, retrying, [dict(r) for r in rows]


def fetch_json(url, *, method="GET", key="", body=None, idem_key=None):
    payload = json.dumps(body).encode() if body is not None else None
    headers = {"Accept": "application/json", "Authorization": f"Bearer {key}"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    if idem_key:
        headers["Idempotency-Key"] = idem_key
    req = Request(url, data=payload, method=method, headers=headers)
    with urlopen(req, timeout=5) as res:
        if res.status < 200 or res.status >= 300:
            raise RuntimeError(f"Unexpected upstream status {res.status}")
        data = res.read(300_000)
        return json.loads(data)


def stock_info(config, sku):
    if not config.stock_url or not config.stock_key:
        raise RuntimeError("Stock API is not configured")
    data = fetch_json(f"{config.stock_url}/{quote(sku, safe='')}", key=config.stock_key)
    if not isinstance(data, dict):
        raise ValueError("Stock API payload was not an object")
    amount = data.get("quantity")
    if isinstance(amount, bool) or not isinstance(amount, (int, float)) or amount < 0:
        raise ValueError("Stock API quantity is invalid")
    result = dict(data)
    result["available"] = amount > 0 and data.get("in_stock", True) is not False
    return result


def send_email(config, delivery, product):
    if not config.resend_url or not config.resend_key:
        raise RuntimeError("Resend API is not configured")
    product_name = product.get("name") if isinstance(product.get("name"), str) else delivery['sku']
    content = ui.email_html(product_name, delivery['sku'], product, config.shop_url)
    payload = {
        "from": config.from_email,
        "to": [delivery['email']],
        "subject": f"It's back in stock: {product_name}",
        "html": content,
        "text": f"Good news! {product_name} ({delivery['sku']}) is back in stock. Visit the store while it lasts.",
    }
    response = fetch_json(f"{config.resend_url}/emails", method="POST", key=config.resend_key,
                          body=payload, idem_key=delivery['idempotency_key'])
    if not isinstance(response, dict) or not response.get('id'):
        raise ValueError("Email provider didn't return an id")
    return str(response['id'])


class Worker:
    def __init__(self, store, config):
        self.store, self.config = store, config
        self.stop_event = threading.Event()
        self.thread = None
        self.product_cache = {}

    def start(self):
        self.thread = threading.Thread(target=self.run, daemon=True, name="outbox-worker")
        self.thread.start()

    def close(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)

    def inspect_sku(self, sku):
        product = stock_info(self.config, sku)
        self.product_cache[sku] = product
        if product['available']:
            self.store.queue_sku(sku)
        return product

    def process_event(self):
        event = self.store.claim_event()
        if not event:
            return False
        try:
            # Quantity is untrusted. A claimed restock *must* be confirmed.
            if event['quantity'] > 0:
                self.inspect_sku(event['sku'])
            self.store.finish_event(event['event_id'])
        except Exception as exc:
            LOG.warning("Stock check for %s failed: %s", event['sku'], exc)
            self.store.finish_event(event['event_id'], error=exc, attempts=event['attempts'] + 1)
        return True

    def process_delivery(self):
        delivery = self.store.claim_delivery()
        if not delivery:
            return False
        try:
            # A confirmed restock already committed the durable delivery. Retry
            # even if it sells out later; it was available when queued.
            product = self.product_cache.get(delivery['sku'], {"name": delivery['sku']})
            provider_id = send_email(self.config, delivery, product)
            self.store.finish_delivery(delivery['id'], delivery['request_id'], provider_id=provider_id)
        except Exception as exc:
            LOG.warning("Email delivery %s retryable failure: %s", delivery['id'], exc)
            self.store.finish_delivery(delivery['id'], delivery['request_id'], error=exc,
                                       attempts=delivery['attempts'] + 1)
        return True

    def run(self):
        next_reconcile = time.monotonic() + 2
        while not self.stop_event.is_set():
            try:
                worked_event = self.process_event()
                worked_delivery = self.process_delivery()
                if time.monotonic() >= next_reconcile:
                    next_reconcile = time.monotonic() + self.config.reconcile_seconds
                    for sku in self.store.open_skus():
                        if self.stop_event.is_set():
                            break
                        try:
                            self.inspect_sku(sku)
                        except Exception as exc:
                            LOG.warning("Reconciliation for %s failed: %s", sku, exc)
                if not worked_event and not worked_delivery:
                    self.stop_event.wait(self.config.poll_seconds)
            except Exception:
                LOG.exception("Worker loop error")
                self.stop_event.wait(1)


class Handler(BaseHTTPRequestHandler):
    server_version = "RestockStudio/1.0"

    @property
    def ctx(self):
        return self.server.context

    def log_message(self, fmt, *args):
        LOG.info("%s %s", self.address_string(), fmt % args)

    def respond(self, status, body, content_type="text/html; charset=utf-8", headers=None):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        framing = "*" if urlsplit(self.path).path == "/embed" else "'none'"
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' https: data:; "
                         "style-src 'self'; script-src 'self'; "
                         f"frame-ancestors {framing}; form-action 'self'")
        if not self.path.startswith("/static/"):
            self.send_header("Cache-Control", "no-store")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def json(self, status, payload):
        self.respond(status, json.dumps(payload, ensure_ascii=False), "application/json; charset=utf-8")

    def parse_json(self):
        if self.headers.get("Content-Type", "").split(";")[0].lower() != "application/json":
            raise ValueError("Content-Type must be application/json")
        length = int(self.headers.get("Content-Length", "0"))
        if length < 1 or length > 32_768:
            raise ValueError("JSON body must be between 1 and 32768 bytes")
        data = json.loads(self.rfile.read(length))
        if not isinstance(data, dict):
            raise ValueError("JSON body must be an object")
        return data

    def parse_form(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length < 1 or length > 8_192:
            raise ValueError("Form body is invalid")
        data = parse_qs(self.rfile.read(length).decode("utf-8"), keep_blank_values=True)
        return {k: v[0] for k, v in data.items() if v}

    def cookie(self, name):
        for item in self.headers.get("Cookie", "").split(";"):
            if item.strip().startswith(name + "="):
                return item.strip()[len(name) + 1:]
        return ""

    def auth_ok(self):
        token = self.cookie("restock_admin")
        try:
            expire_str, signature = token.split(".", 1)
            if int(expire_str) < time.time():
                return False
            want = hmac.new(self.ctx.config.admin_password.encode(),
                            f"restock_admin:{expire_str}".encode(), hashlib.sha256).hexdigest()
            return hmac.compare_digest(want, signature)
        except (ValueError, AttributeError):
            return False

    def new_cookie(self):
        expires = str(int(time.time()) + 60 * 60 * 12)
        signature = hmac.new(self.ctx.config.admin_password.encode(),
                             f"restock_admin:{expires}".encode(), hashlib.sha256).hexdigest()
        secure = "; Secure" if self.headers.get("X-Forwarded-Proto", "") == "https" else ""
        return f"restock_admin={expires}.{signature}; HttpOnly; SameSite=Lax; Path=/admin; Max-Age=43200{secure}"

    def do_GET(self):
        url = urlsplit(self.path)
        path = url.path
        if path == "/healthz":
            return self.respond(200, "ok", "text/plain; charset=utf-8")
        if path == "/":
            return self.respond(200, ui.home_page())
        if path == "/embed":
            params = parse_qs(url.query)
            sku = normalize_sku(params.get('sku', [''])[0]) or ""
            return self.respond(200, ui.embed_page(sku))
        if path == "/admin/login":
            if self.auth_ok():
                return self.respond(303, "", headers={"Location": "/admin"})
            return self.respond(200, ui.login_page())
        if path == "/admin":
            if not self.auth_ok():
                return self.respond(303, "", headers={"Location": "/admin/login"})
            filters = parse_qs(url.query)
            status = filters.get('status', ['all'])[0]
            stats, retrying, rows = self.ctx.store.dashboard(status)
            return self.respond(200, ui.admin_page(stats, retrying, rows, status))
        allowed = {"/static/style.css": ("text/css; charset=utf-8", "style.css"),
                   "/static/embed.js": ("application/javascript; charset=utf-8", "embed.js")}
        if path in allowed:
            media_type, filename = allowed[path]
            return self.respond(200, (ROOT / "static" / filename).read_bytes(), media_type,
                                headers={"Cache-Control": "public, max-age=3600"})
        return self.json(404, {"error": "Not found"})

    def do_POST(self):
        path = urlsplit(self.path).path
        if path == "/api/requests":
            try:
                data = self.parse_json()
            except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
                return self.json(400, {"error": str(exc)})
            raw_email = data.get('email')
            sku = normalize_sku(data.get('sku'))
            email = raw_email.strip().lower() if isinstance(raw_email, str) else None
            if not is_valid_email(email) or not sku:
                return self.json(422, {"error": "Provide a valid email and SKU."})
            created, row = self.ctx.store.add_request(email, sku)
            return self.json(201 if created else 200,
                             {"ok": True, "duplicate": not created, "status": row['status'], "id": row['id']})
        if path == "/webhooks/stock":
            expected = self.ctx.config.webhook_secret
            submitted = self.headers.get("X-Webhook-Secret", "")
            if not expected or not hmac.compare_digest(expected, submitted):
                return self.json(401, {"error": "Unauthorized webhook"})
            try:
                data = self.parse_json()
            except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
                return self.json(400, {"error": str(exc)})
            event_id = data.get("event_id")
            sku = normalize_sku(data.get("sku"))
            quantity = data.get("quantity")
            if (not isinstance(event_id, str) or not 1 <= len(event_id) <= 128 or
                    not sku or isinstance(quantity, bool) or
                    not isinstance(quantity, (int, float)) or quantity < 0 or quantity > 1_000_000):
                return self.json(422, {"error": "Invalid event_id, sku, or quantity"})
            if not isinstance(quantity, int) and not quantity.is_integer():
                return self.json(422, {"error": "Quantity must be a whole number"})
            inserted = self.ctx.store.add_event(event_id, sku, int(quantity))
            return self.json(202, {"ok": True, "duplicate_event": not inserted})
        if path == "/admin/login":
            try:
                data = self.parse_form()
            except ValueError:
                return self.respond(400, ui.login_page(error="Invalid login request"))
            entered = data.get('password', '')
            if not self.ctx.config.admin_password or not hmac.compare_digest(
                    entered, self.ctx.config.admin_password):
                return self.respond(401, ui.login_page(error="Incorrect password"))
            return self.respond(303, "", headers={"Location": "/admin", "Set-Cookie": self.new_cookie()})
        if path == "/admin/logout":
            return self.respond(303, "", headers={"Location": "/admin/login", "Set-Cookie":
                                  "restock_admin=; HttpOnly; SameSite=Lax; Path=/admin; Max-Age=0"})
        return self.json(404, {"error": "Not found"})


class Context:
    def __init__(self, config):
        self.config = config
        self.store = Store(config.db_path)
        self.worker = Worker(self.store, config)


def build_server(config, host="0.0.0.0", port=None):
    ctx = Context(config)
    server = ThreadingHTTPServer((host, config.port if port is None else port), Handler)
    server.daemon_threads = True
    server.context = ctx
    return server


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    config = Config()
    for key in ("STOCK_API_URL", "STOCK_API_KEY", "RESEND_API_KEY", "RESEND_BASE_URL", "WEBHOOK_SECRET"):
        if not os.getenv(key):
            LOG.warning("Missing configuration: %s", key)
    server = build_server(config)
    server.context.worker.start()
    LOG.info("Restock Studio listening on http://0.0.0.0:%s", server.server_port)
    try:
        server.serve_forever(poll_interval=0.3)
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.context.worker.close()
        server.server_close()


if __name__ == "__main__":
    main()
