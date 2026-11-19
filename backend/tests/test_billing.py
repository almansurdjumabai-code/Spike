"""server/billing.py: Paddle webhooks, signatures and the user's plan."""

import hashlib
import hmac
import json
import time

from fastapi import FastAPI
from fastapi.testclient import TestClient

from server import accounts, billing, cloud

SECRET = "pdl_ntfset_test_secret"
PRICES = {
    "PADDLE_PRICE_PRO_MONTHLY": "pri_pro_m",
    "PADDLE_PRICE_PRO_YEARLY": "pri_pro_y",
    "PADDLE_PRICE_MAX_MONTHLY": "pri_max_m",
    "PADDLE_PRICE_MAX_YEARLY": "pri_max_y",
}


def _sign(body: bytes, ts: int | None = None, secret: str = SECRET) -> str:
    ts = ts or int(time.time())
    h = hmac.new(secret.encode(), f"{ts}:".encode() + body, hashlib.sha256).hexdigest()
    return f"ts={ts};h1={h}"


def _event(kind="subscription.created", status="active", price="pri_pro_m", user=1, sub="sub_1",
           at="2026-11-20T10:00:00Z"):
    return {
        "event_type": kind,
        "occurred_at": at,
        "data": {
            "id": sub, "status": status, "customer_id": "ctm_1", "custom_data": {"user_id": user},
            "items": [{"price": {"id": price}}],
            "current_billing_period": {"ends_at": "2026-12-20T10:00:00Z"},
            "management_urls": {"cancel": "https://paddle.test/cancel", "update_payment_method": "https://paddle.test/upd"},
        },
    }


def _client(monkeypatch, tmp_path):
    monkeypatch.setenv("SPIKECLIP_API_TOKEN", "admin")
    monkeypatch.setenv("SPIKECLIP_OPEN_SIGNUP", "1")
    monkeypatch.setenv("PADDLE_WEBHOOK_SECRET", SECRET)
    monkeypatch.setenv("PADDLE_CLIENT_TOKEN", "test_abc")
    for k, v in PRICES.items():
        monkeypatch.setenv(k, v)
    app = FastAPI()
    cloud.install_auth(app)
    acc = accounts.install(app, tmp_path)
    monkeypatch.setattr(cloud, "SESSION_CHECK", acc.session_valid)
    billing.install(app, tmp_path, acc.user_for)
    return TestClient(app, base_url="http://127.0.0.1")


def _post(client, event, header=None):
    body = json.dumps(event).encode()
    return client.post("/billing/paddle/webhook", content=body,
                       headers={"Paddle-Signature": header or _sign(body), "Content-Type": "application/json"})


def test_config_is_public_and_complete(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    cfg = client.get("/billing/config").json()
    assert cfg["enabled"] and cfg["environment"] == "sandbox" and cfg["prices"]["max_yearly"] == "pri_max_y"


def test_a_bad_or_stale_signature_is_refused(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    body = json.dumps(_event()).encode()
    assert _post(client, _event(), header=_sign(body, secret="wrong")).status_code == 401
    assert _post(client, _event(), header=_sign(body, ts=int(time.time()) - 3600)).status_code == 401
    assert _post(client, _event(), header="nonsense").status_code == 401


def test_a_subscription_upgrades_the_user_and_cancelling_ends_it(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    token = client.post("/auth/register", json={"email": "a@b.co", "password": "longenough"}).json()["token"]
    me = lambda: client.get("/billing/me", headers={"Authorization": f"Bearer {token}"}).json()  # noqa: E731
    assert me()["plan"] == "free"
    assert _post(client, _event(user=1)).json()["stored"]
    got = me()
    assert got["plan"] == "pro" and got["renews_at"] == "2026-12-20" and got["cancel_url"]
    assert _post(client, _event("subscription.updated", price="pri_max_y", at="2026-11-21T10:00:00Z")).json()["stored"]
    assert me()["plan"] == "max"
    # A late, older event does not roll the plan back.
    assert not _post(client, _event("subscription.updated", price="pri_pro_m", at="2026-11-20T11:00:00Z")).json()["stored"]
    assert me()["plan"] == "max"
    _post(client, _event("subscription.canceled", status="canceled", price="pri_max_y", at="2026-11-22T10:00:00Z"))
    assert me()["plan"] == "free"


def test_unknown_prices_and_other_events_are_ignored(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    assert not _post(client, _event(price="pri_someone_else")).json()["stored"]
    assert not _post(client, {"event_type": "transaction.completed", "data": {}}).json()["stored"]
