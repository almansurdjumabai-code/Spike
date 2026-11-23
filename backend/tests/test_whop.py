"""Whop: signed membership webhooks issue and stop keys; buyers claim them by email."""

import base64
import hashlib
import hmac
import json
import time

import pytest
from fastapi.testclient import TestClient

from app.db import Database
from app.main import create_app

SECRET = "whsec_" + base64.b64encode(b"whop-test-secret").decode()
MONTHLY = "prod_o2igFfiAXZMKB"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("WHOP_WEBHOOK_SECRET", SECRET)
    monkeypatch.setenv("LICENSE_RATE_PER_MINUTE", "1000")
    for k in ("SIGNUP", "SPIKECLIP_OPEN_SIGNUP", "INVITE_CODE", "SPIKECLIP_INVITE_CODE", "BILLING_PROVIDER"):
        monkeypatch.delenv(k, raising=False)
    return TestClient(create_app(Database(f"sqlite:///{tmp_path / 'api.db'}")))


def send(client, kind, mem="mem_1", email="fan@example.com", product=MONTHLY, status="active", msg=None,
         secret=SECRET, ts=None):
    body = json.dumps({"type": kind, "data": {"id": mem, "status": status, "product": {"id": product},
                                               "user": {"id": "user_1", "email": email}}}).encode()
    msg = msg or f"msg_{kind}_{mem}_{status}"
    ts = str(ts or int(time.time()))
    key = base64.b64decode(secret[len("whsec_"):])
    sig = base64.b64encode(hmac.new(key, f"{msg}.{ts}.".encode() + body, hashlib.sha256).digest()).decode()
    return client.post("/billing/whop/webhook", content=body,
                       headers={"webhook-id": msg, "webhook-timestamp": ts, "webhook-signature": f"v1,{sig}"})


def my_keys(client, token):
    return client.get("/licenses/me", headers={"Authorization": f"Bearer {token}"}).json()["licenses"]


def register(client, email="fan@example.com"):
    r = client.post("/auth/register", json={"email": email, "password": "longenough", "name": "Fan"})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def test_bad_or_old_signature_is_rejected(client):
    assert send(client, "membership.activated", secret="whsec_" + base64.b64encode(b"wrong").decode()).status_code == 401
    assert send(client, "membership.activated", ts=int(time.time()) - 3600).status_code == 401


def test_buyer_without_account_claims_the_key_on_signup(client):
    assert send(client, "membership.activated").json()["result"] == "created"
    token = register(client)
    keys = my_keys(client, token)
    assert len(keys) == 1 and keys[0]["plan"] == "pro" and keys[0]["state"] == "ok"
    # The key works in the desktop app.
    r = client.post("/v1/license/activate", json={"key": keys[0]["key"], "device_id": "pc-1-abcdef123456"})
    assert r.json()["code"] == "ok"


def test_existing_account_gets_the_key_and_deactivation_stops_it(client):
    token = register(client)
    send(client, "membership.activated")
    key = my_keys(client, token)[0]["key"]
    assert send(client, "membership.activated").json()["result"] == "duplicate"
    assert send(client, "membership.deactivated", status="canceled").json()["result"] == "stopped"
    assert client.post("/v1/license/validate", json={"key": key, "device_id": "pc-1-abcdef123456"}).json()["code"] != "ok"
    # Coming back on the same membership turns it on again.
    assert send(client, "membership.updated", status="active", msg="msg_again").json()["result"] == "updated"
    assert my_keys(client, token)[0]["state"] == "ok"


def test_unknown_products_and_other_events_are_ignored(client):
    assert send(client, "membership.activated", product="prod_someone_else").json()["result"] == "ignored"
    assert send(client, "payment.succeeded").json()["result"] == "ignored"


def test_config_prefers_whop_checkout(client):
    cfg = client.get("/billing/config").json()
    assert cfg["provider"] == "whop" and cfg["whop"]["checkout"]["pro_monthly"].startswith("https://whop.com/")
