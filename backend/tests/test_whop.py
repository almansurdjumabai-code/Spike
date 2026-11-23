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
    # Any product of our own (signed) company is Pro by default.
    assert send(client, "membership.activated", product="prod_new_one").json()["result"] == "created"
    assert send(client, "payment.failed").json()["result"] == "ignored"


def test_config_prefers_whop_checkout(client):
    cfg = client.get("/billing/config").json()
    assert cfg["provider"] == "whop" and cfg["whop"]["checkout"]["pro_monthly"].startswith("https://whop.com/")


def send_payment(client, kind="payment.succeeded", msg="msg_pay_1", email="fan@example.com"):
    """Shaped like Whop's v1 payment webhook: ids nested under membership/product/user."""
    body = json.dumps({
        "account_id": "biz_x", "api_version": "v1", "type": kind,
        "data": {"id": "pay_1", "status": "paid", "amount_after_fees": {"amount": "0.00"},
                 "membership": {"id": "mem_pay", "status": "active"}, "product": {"id": MONTHLY, "title": "Pro"},
                 "plan": {"id": "plan_1"}, "user": {"id": "user_9", "email": email, "username": "fan"}},
    }).encode()
    ts = str(int(time.time()))
    key = base64.b64decode(SECRET[len("whsec_"):])
    sig = base64.b64encode(hmac.new(key, f"{msg}.{ts}.".encode() + body, hashlib.sha256).digest()).decode()
    return client.post("/billing/whop/webhook", content=body,
                       headers={"webhook-id": msg, "webhook-timestamp": ts, "webhook-signature": f"v1,{sig}"})


def test_payment_events_issue_and_refunds_stop_the_key(client):
    token = register(client)
    assert send_payment(client, "payment.failed", msg="m0").json()["result"] == "ignored"
    assert send_payment(client).json()["result"] == "created"
    assert my_keys(client, token)[0]["state"] == "ok"
    assert send_payment(client, "payment.refunded", msg="m2").json()["result"] == "stopped"


def test_an_ignored_event_can_be_replayed_after_a_fix(client):
    assert send_payment(client, "payment.pending", msg="same").json()["result"] == "ignored"
    assert send_payment(client, msg="same").json()["result"] == "created"


def test_real_payment_payload_and_email_backfill_on_replay(client):
    """Trimmed from a real Whop payment.succeeded: email in customer_email, ids as flat strings."""
    token = register(client, "buyer@example.ru")
    payload = {"account_id": "biz_7IVEABBhVVI2FS", "api_version": "v1", "type": "payment.succeeded",
               "id": "msg_real", "data": {"id": "pay_1", "customer_email": "buyer@example.ru",
               "membership_id": "mem_TFq1", "product_id": MONTHLY, "status": "paid",
               "line_items": [{"product_id": MONTHLY, "variant_id": "plan_1"}],
               "user": {"id": "user_1", "username": "fan"}}}

    def post(msg):
        body = json.dumps(payload).encode()
        ts = str(int(time.time()))
        key = base64.b64decode(SECRET[len("whsec_"):])
        sig = base64.b64encode(hmac.new(key, f"{msg}.{ts}.".encode() + body, hashlib.sha256).digest()).decode()
        return client.post("/billing/whop/webhook", content=body,
                           headers={"webhook-id": msg, "webhook-timestamp": ts, "webhook-signature": f"v1,{sig}"})

    r = post("msg_real").json()
    assert r["result"] == "created" and r["email_found"] and r["membership_found"]
    assert my_keys(client, token)[0]["state"] == "ok"


def test_replay_links_a_key_created_without_email(tmp_path, monkeypatch):
    from app import licenses
    monkeypatch.setenv("WHOP_WEBHOOK_SECRET", SECRET)
    db = Database(f"sqlite:///{tmp_path / 'replay.db'}")
    client = TestClient(create_app(db))
    token = register(client, "buyer@example.ru")
    with db.connect() as c:
        licenses.issue(c, plan="pro", user_id=None, email=None, source="whop", subscription_id="whop:mem_old")
        c.execute("INSERT INTO paddle_events VALUES (?, ?, ?)", ("whop:msg_old", "payment.succeeded", 0))
    body = json.dumps({"type": "payment.succeeded", "data": {"customer_email": "buyer@example.ru",
                       "membership_id": "mem_old", "product_id": MONTHLY}}).encode()
    ts = str(int(time.time()))
    key = base64.b64decode(SECRET[len("whsec_"):])
    sig = base64.b64encode(hmac.new(key, f"msg_old.{ts}.".encode() + body, hashlib.sha256).digest()).decode()
    r = client.post("/billing/whop/webhook", content=body,
                    headers={"webhook-id": "msg_old", "webhook-timestamp": ts, "webhook-signature": f"v1,{sig}"})
    assert r.json()["result"] == "duplicate (email linked)"
    assert len(my_keys(client, token)) == 1


def test_event_marked_seen_without_a_key_is_applied_on_replay(tmp_path, monkeypatch):
    """The first live delivery was recorded as seen by an older version that skipped payments."""
    monkeypatch.setenv("WHOP_WEBHOOK_SECRET", SECRET)
    db = Database(f"sqlite:///{tmp_path / 'seen.db'}")
    client = TestClient(create_app(db))
    token = register(client, "buyer@example.ru")
    with db.connect() as c:
        c.execute("INSERT INTO paddle_events VALUES (?, ?, ?)", ("whop:msg_first", "payment.succeeded", 0))
    body = json.dumps({"type": "payment.succeeded", "data": {"customer_email": "buyer@example.ru",
                       "membership_id": "mem_first", "product_id": MONTHLY}}).encode()

    def post():
        ts = str(int(time.time()))
        key = base64.b64decode(SECRET[len("whsec_"):])
        sig = base64.b64encode(hmac.new(key, f"msg_first.{ts}.".encode() + body, hashlib.sha256).digest()).decode()
        return client.post("/billing/whop/webhook", content=body, headers={
            "webhook-id": "msg_first", "webhook-timestamp": ts, "webhook-signature": f"v1,{sig}"}).json()["result"]

    assert post() == "created"
    assert my_keys(client, token)[0]["state"] == "ok"
    assert post() == "duplicate"  # and only one key
    assert len(my_keys(client, token)) == 1
