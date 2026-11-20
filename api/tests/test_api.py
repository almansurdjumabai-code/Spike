"""SpikeClip web API: accounts, Paddle webhooks, licence keys, admin."""

import hashlib
import hmac
import json
import time

import pytest
from fastapi.testclient import TestClient

from app import licenses
from app.db import Database
from app.main import create_app

SECRET = "pdl_ntfset_test"
PRO_M = "pri_01m7t5x5gssxg4xm7jr3t88j6v"
MAX_Y = "pri_01m7t63qmhgx9m07pan3w0d4y3"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("PADDLE_WEBHOOK_SECRET", SECRET)
    monkeypatch.setenv("ADMIN_TOKEN", "owner-token")
    monkeypatch.setenv("LICENSE_RATE_PER_MINUTE", "1000")
    for k in ("SIGNUP", "SPIKECLIP_OPEN_SIGNUP", "INVITE_CODE", "SPIKECLIP_INVITE_CODE"):
        monkeypatch.delenv(k, raising=False)
    return TestClient(create_app(Database(f"sqlite:///{tmp_path / 'api.db'}")))


def signup(client, email="buyer@example.com"):
    r = client.post("/auth/register", json={"email": email, "password": "longenough", "name": "Buyer"})
    assert r.status_code == 200, r.text
    return r.json()["token"], r.json()["user"]["id"]


def webhook(client, kind="subscription.created", status="active", price=PRO_M, user=1, sub="sub_1",
            at="2026-11-20T10:00:00Z", ends="2099-01-01T00:00:00Z", event_id=None):
    event = {
        "event_id": event_id or f"evt_{kind}_{at}",
        "event_type": kind,
        "occurred_at": at,
        "data": {
            "id": sub, "status": status, "customer_id": "ctm_1", "custom_data": {"user_id": user},
            "items": [{"price": {"id": price}}], "current_billing_period": {"ends_at": ends},
            "management_urls": {"cancel": "https://pdl/cancel", "update_payment_method": "https://pdl/upd"},
        },
    }
    body = json.dumps(event).encode()
    ts = int(time.time())
    sig = hmac.new(SECRET.encode(), f"{ts}:".encode() + body, hashlib.sha256).hexdigest()
    return client.post("/billing/paddle/webhook", content=body, headers={"Paddle-Signature": f"ts={ts};h1={sig}"})


def act(client, key, device="device-aaaaaaaa", path="activate"):
    return client.post(f"/v1/license/{path}", json={"key": key, "device_id": device, "device_name": "PC",
                                                    "platform": "windows", "app_version": "2.1.0"}).json()


def test_health_and_signup_is_open_by_default(client):
    assert client.get("/health").json()["ok"]
    assert client.get("/auth/config").json() == {"signup": "open"}
    token, _ = signup(client)
    assert client.get("/auth/check", headers={"Authorization": f"Bearer {token}"}).status_code == 200
    assert client.get("/auth/check").status_code == 401


def test_key_format():
    for _ in range(50):
        k = licenses.new_key()
        assert licenses.KEY_RE.match(k) and not set(k[5:]) & set("01OIL")
    assert licenses.normalize_key("clip-abcd efgh-2345") == "CLIP-ABCD-EFGH-2345"


def test_purchase_creates_a_key_that_activates_up_to_the_device_limit(client):
    token, uid = signup(client)
    auth = {"Authorization": f"Bearer {token}"}
    assert webhook(client, user=uid).json()["result"] == "created"
    keys = client.get("/licenses/me", headers=auth).json()["licenses"]
    assert len(keys) == 1 and keys[0]["plan"] == "pro" and keys[0]["state"] == "ok"
    key = keys[0]["key"]
    assert licenses.KEY_RE.match(key)

    first = act(client, key, "device-aaaaaaaa")
    assert first["ok"] and first["code"] == "ok" and first["license"]["activations_used"] == 1
    assert act(client, key, "device-aaaaaaaa")["ok"]  # the same PC again does not use a slot
    assert act(client, key, "device-bbbbbbbb")["ok"]
    limit = act(client, key, "device-cccccccc")
    assert not limit["ok"] and limit["code"] == "activation_limit"

    assert act(client, key, "device-aaaaaaaa", "validate")["code"] == "ok"
    assert act(client, key, "device-cccccccc", "validate")["code"] == "not_activated"
    assert act(client, key, "device-aaaaaaaa", "deactivate")["ok"]
    assert act(client, key, "device-cccccccc")["ok"]

    # The account page can release a device too.
    dev = client.get("/licenses/me", headers=auth).json()["licenses"][0]["devices"][0]["device"]
    assert client.delete(f"/licenses/{key}/devices/{dev}", headers=auth).status_code == 200
    assert client.get("/billing/me", headers=auth).json()["plan"] == "pro"


def test_unknown_keys_and_cancelled_subscriptions(client):
    assert act(client, "CLIP-AAAA-BBBB-CCCC")["code"] == "invalid_key"
    token, uid = signup(client)
    webhook(client, user=uid, price=MAX_Y)
    key = client.get("/licenses/me", headers={"Authorization": f"Bearer {token}"}).json()["licenses"][0]["key"]
    assert act(client, key)["license"]["plan"] == "max"
    # A late, older event is ignored; a cancellation that already ended expires the key.
    assert webhook(client, "subscription.updated", at="2026-11-19T00:00:00Z").json()["result"] == "stale"
    webhook(client, "subscription.canceled", status="canceled", price=MAX_Y, at="2026-11-21T00:00:00Z",
            ends="2020-01-01T00:00:00Z")
    got = act(client, key, path="validate")
    assert not got["ok"] and got["code"] in ("expired", "inactive")


def test_webhooks_must_be_signed_and_are_applied_once(client):
    body = b'{"event_type":"subscription.created"}'
    bad = client.post("/billing/paddle/webhook", content=body, headers={"Paddle-Signature": "ts=1;h1=00"})
    assert bad.status_code == 401
    _, uid = signup(client)
    assert webhook(client, user=uid, event_id="evt_same").json()["result"] == "created"
    assert webhook(client, user=uid, event_id="evt_same").json()["result"] == "duplicate"
    assert webhook(client, price="pri_unknown", sub="sub_2", event_id="evt_x").json()["result"] == "ignored"


def test_admin_issues_and_revokes(client):
    owner = {"Authorization": "Bearer owner-token"}
    assert client.post("/admin/licenses", json={"plan": "pro"}).status_code == 401
    lic = client.post("/admin/licenses", json={"plan": "pro", "email": "friend@x.co", "days": 30}, headers=owner).json()
    assert act(client, lic["key"])["ok"]
    client.post(f"/admin/licenses/{lic['key']}/revoke", headers=owner)
    assert act(client, lic["key"], path="validate")["code"] == "revoked"
    assert len(client.get("/admin/licenses", headers=owner).json()["licenses"]) == 1


def test_paddle_config_has_live_defaults(client, monkeypatch):
    for k in ("PADDLE_ENV", "PADDLE_CLIENT_TOKEN"):
        monkeypatch.delenv(k, raising=False)
    cfg = client.get("/billing/config").json()
    assert cfg["enabled"] and cfg["environment"] == "production" and cfg["prices"]["pro_monthly"] == PRO_M
