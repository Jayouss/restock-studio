"""Integration tests using a local, dependency-free mock of the challenge harness."""
import http.client
import json
import socket
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app import Config, build_server


class FakeHarness:
    def __init__(self):
        self.lock = threading.Lock()
        self.stock = {"ITEM-A": 0, "ITEM-B": 0}
        self.fail_remaining = 0
        self.drop_after_accept = False
        self.accepted = {}
        self.email_calls = []
        self.stock_calls = []


class MockHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        return

    def json(self, status, data):
        payload = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.headers.get("Authorization") != "Bearer stock-key":
            return self.json(401, {"error": "unauthorized"})
        sku = self.path.removeprefix("/api/stock/")
        with self.server.state.lock:
            self.server.state.stock_calls.append(sku)
            amount = self.server.state.stock.get(sku, 0)
        self.json(200, {"sku": sku, "name": "Fancy Sample Item", "quantity": amount,
                        "in_stock": amount > 0, "currency": "GBP", "price": 29})

    def do_POST(self):
        if self.path != "/emails":
            return self.json(404, {"error": "not found"})
        if self.headers.get('Authorization') != 'Bearer resend-key':
            return self.json(401, {"error": "unauthorized"})
        data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        key = self.headers.get("Idempotency-Key")
        with self.server.state.lock:
            self.server.state.email_calls.append({"key": key, "payload": data})
            if key in self.server.state.accepted:
                provider = self.server.state.accepted[key]
                return self.json(200, {"id": provider})
            if self.server.state.fail_remaining:
                self.server.state.fail_remaining -= 1
                return self.json(500, {"error": "Temporary failure"})
            provider = f"email-{len(self.server.state.accepted) + 1}"
            self.server.state.accepted[key] = provider
            drop = self.server.state.drop_after_accept
            self.server.state.drop_after_accept = False
        if drop:
            self.connection.shutdown(socket.SHUT_RDWR)
            self.connection.close()
            return
        self.json(200, {"id": provider})


def api_request(url, body=None, secret=None, method=None, headers=None):
    head = dict(headers or {})
    payload = json.dumps(body).encode() if body is not None else None
    if body is not None:
        head['Content-Type'] = 'application/json'
    if secret is not None:
        head['X-Webhook-Secret'] = secret
    req = Request(url, data=payload, method=method or ('POST' if body is not None else 'GET'), headers=head)
    try:
        with urlopen(req, timeout=5) as response:
            return response.status, response.read().decode(), dict(response.headers)
    except HTTPError as response:
        return response.code, response.read().decode(), dict(response.headers)


def eventually(condition, timeout=9):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if condition():
            return
        time.sleep(0.08)
    raise AssertionError("Condition was not met in time")


class RestockIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.harness_state = FakeHarness()
        self.harness = ThreadingHTTPServer(('127.0.0.1', 0), MockHandler)
        self.harness.state = self.harness_state
        self.harness_thread = threading.Thread(target=self.harness.serve_forever, daemon=True)
        self.harness_thread.start()
        harness_origin = f"http://127.0.0.1:{self.harness.server_port}"
        self.env = {
            "PORT": "0", "DB_PATH": str(Path(self.directory.name)/'test.sqlite3'),
            "STOCK_API_URL": harness_origin + '/api/stock',
            "STOCK_API_KEY": "stock-key", "RESEND_BASE_URL": harness_origin,
            "RESEND_API_KEY": "resend-key", "WEBHOOK_SECRET": "whsec-test-123",
            "ADMIN_PASSWORD": "super-secure-test-password", "RECONCILE_SECONDS": "1.5", "POLL_SECONDS": "0.05",
        }
        self.start_app()

    def tearDown(self):
        self.stop_app()
        self.harness.shutdown()
        self.harness.server_close()
        self.harness_thread.join(timeout=3)
        self.directory.cleanup()

    def start_app(self):
        self.config = Config(self.env)
        self.app = build_server(self.config, host='127.0.0.1', port=0)
        self.origin = f'http://127.0.0.1:{self.app.server_port}'
        self.app.context.worker.start()
        self.thread = threading.Thread(target=self.app.serve_forever, daemon=True)
        self.thread.start()

    def stop_app(self):
        self.app.shutdown()
        self.app.context.worker.close()
        self.app.server_close()
        self.thread.join(timeout=3)

    def subscribe(self, email='person@example.com', sku='ITEM-A'):
        return api_request(self.origin+'/api/requests', {"email": email, "sku": sku})

    def webhook(self, event_id='event-1', sku='ITEM-A', quantity=10, secret='whsec-test-123'):
        return api_request(self.origin+'/webhooks/stock',
                           {"event_id": event_id, "sku": sku, "quantity": quantity}, secret=secret)

    def test_endpoints_and_admin_protection(self):
        status, body, _ = api_request(self.origin+'/embed?sku=ITEM-A')
        self.assertEqual(status, 200)
        self.assertIn('name="sku"', body)
        self.assertIn('ITEM-A', body)
        status, body, headers = api_request(self.origin+'/admin')
        self.assertEqual(status, 200)  # urllib automatically follows redirect to /admin/login
        self.assertIn('Admin password', body)
        status, body, _ = self.webhook(secret='wrong')
        self.assertEqual(status, 401)
        self.assertEqual(len(self.harness_state.stock_calls), 0)

    def test_admin_password_and_session_cookie(self):
        conn = http.client.HTTPConnection('127.0.0.1', self.app.server_port, timeout=5)
        conn.request('POST', '/admin/login', 'password=super-secure-test-password',
                     {'Content-Type': 'application/x-www-form-urlencoded'})
        response = conn.getresponse()
        self.assertEqual(response.status, 303)
        token = response.getheader('Set-Cookie').split(';', 1)[0]
        response.read()
        conn.request('GET', '/admin', headers={'Cookie': token})
        response = conn.getresponse()
        text = response.read().decode()
        self.assertEqual(response.status, 200)
        self.assertIn('Alert activity', text)
        self.assertIn('Waiting for stock', text)
        conn.close()

    def test_concurrent_duplicate_signups(self):
        with ThreadPoolExecutor(max_workers=12) as pool:
            results = list(pool.map(lambda _: self.subscribe(), range(18)))
        self.assertEqual(sum(status == 201 for status, _, _ in results), 1)
        self.assertTrue(all(status in (200,201) for status, _, _ in results))
        stats, _, _ = self.app.context.store.dashboard()
        self.assertEqual(stats.get('open'), 1)

    def test_phantom_and_duplicate_webhooks_then_one_email(self):
        self.assertEqual(self.subscribe()[0], 201)
        self.webhook(event_id='phantom-1')
        eventually(lambda: len(self.harness_state.stock_calls) > 0)
        time.sleep(0.2)
        self.assertEqual(len(self.harness_state.accepted), 0,
                         'Never trust a claimed restock when real stock is zero')
        with self.harness_state.lock:
            self.harness_state.stock['ITEM-A'] = 20
        with ThreadPoolExecutor(max_workers=10) as pool:
            results = list(pool.map(lambda _: self.webhook('restock-shared-id'), range(10)))
        self.assertTrue(all(code == 202 for code, _, _ in results))
        eventually(lambda: len(self.harness_state.accepted) == 1)
        time.sleep(0.5)
        self.assertEqual(len(self.harness_state.accepted), 1)
        stats, _, requests = self.app.context.store.dashboard()
        self.assertEqual(stats.get('notified'), 1)
        self.assertIsNotNone(requests[0]['notified_at'])
        self.assertIn('Fancy Sample Item', self.harness_state.email_calls[0]['payload']['html'])
        self.assertIn('width="100%"', self.harness_state.email_calls[0]['payload']['html'])

    def test_retry_on_provider_500_with_stable_idempotency_key(self):
        self.harness_state.fail_remaining = 1
        self.subscribe()
        with self.harness_state.lock:
            self.harness_state.stock['ITEM-A'] = 1
        self.webhook('event-retry')
        eventually(lambda: len(self.harness_state.accepted) == 1, timeout=9)
        self.assertGreaterEqual(len(self.harness_state.email_calls), 2)
        keys = {item['key'] for item in self.harness_state.email_calls}
        self.assertEqual(len(keys), 1)
        stats, retrying, _ = self.app.context.store.dashboard()
        self.assertEqual(stats.get('notified'), 1)
        self.assertEqual(retrying, 0)

    def test_unknown_send_outcome_is_deduped_on_retry(self):
        """Provider accepts email but network drops before the response reaches us."""
        self.harness_state.drop_after_accept = True
        self.subscribe('uncertain@example.com')
        with self.harness_state.lock:
            self.harness_state.stock['ITEM-A'] = 3
        self.webhook('event-ambiguous-network')
        eventually(lambda: len(self.harness_state.email_calls) >= 2, timeout=9)
        eventually(lambda: self.app.context.store.dashboard()[0].get('notified') == 1)
        self.assertEqual(len(self.harness_state.accepted), 1)
        self.assertEqual(len({x['key'] for x in self.harness_state.email_calls}), 1)

    def test_invalid_requests_are_rejected_without_database_changes(self):
        code, _, _ = self.subscribe('not-an-email', 'ITEM-A')
        self.assertEqual(code, 422)
        code, _, _ = self.subscribe('valid@example.com', '<script>')
        self.assertEqual(code, 422)
        stats, _, _ = self.app.context.store.dashboard()
        self.assertEqual(stats, {})

    def test_sqlite_state_survives_restart_and_reconciliation(self):
        self.assertEqual(self.subscribe('restart@example.com', 'ITEM-B')[0], 201)
        self.stop_app()
        self.start_app()
        stats, _, _ = self.app.context.store.dashboard()
        self.assertEqual(stats.get('open'), 1)
        with self.harness_state.lock:
            self.harness_state.stock['ITEM-B'] = 8
        eventually(lambda: len(self.harness_state.accepted) == 1, timeout=8)
        stats, _, _ = self.app.context.store.dashboard()
        self.assertEqual(stats.get('notified'), 1)


if __name__ == '__main__':
    unittest.main()
