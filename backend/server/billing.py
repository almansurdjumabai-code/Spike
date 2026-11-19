"""Subscriptions through Paddle Billing (paddle.com), for the web app.

Paddle is the merchant of record: it runs the checkout, charges the card,
handles sales tax / VAT and refunds, and tells this server what happened
through signed webhooks. This module keeps one row per subscription and
answers "which plan is this user on?".

Configuration. The public values (client token, price ids) have defaults
below for SpikeClip's live Paddle account; an environment variable of the
same name overrides each. Only the webhook secret must be set on the host:

    PADDLE_ENV                 "production" (default) or "sandbox"
    PADDLE_CLIENT_TOKEN        client-side token (public; starts test_/live_)
    PADDLE_WEBHOOK_SECRET      the notification destination's secret key
    PADDLE_PRICE_PRO_MONTHLY   price ids (pri_...) from the Paddle catalog
    PADDLE_PRICE_PRO_YEARLY
    PADDLE_PRICE_MAX_MONTHLY
    PADDLE_PRICE_MAX_YEARLY

Webhook URL to register in Paddle: <backend>/billing/paddle/webhook
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException, Request

PLANS = ("free", "pro", "max")
# Public by design: the client token is sent to every browser that opens
# checkout, and price ids appear in it too. The webhook secret is NOT here.
DEFAULTS = {
    "PADDLE_ENV": "production",
    "PADDLE_CLIENT_TOKEN": "live_34e224b5ac701715da2f516291c",
    "PADDLE_PRICE_PRO_MONTHLY": "pri_01m7t5x5gssxg4xm7jr3t88j6v",
    "PADDLE_PRICE_PRO_YEARLY": "pri_01m7t62md9gyh9msbq36ycvrjq",
    "PADDLE_PRICE_MAX_MONTHLY": "pri_01m7t5y7dvkd5h42bgve5gh0r4",
    "PADDLE_PRICE_MAX_YEARLY": "pri_01m7t63qmhgx9m07pan3w0d4y3",
}


def setting(name: str) -> str:
    return os.environ.get(name) or DEFAULTS.get(name, "")


PRICE_ENV = {
    ("pro", "monthly"): "PADDLE_PRICE_PRO_MONTHLY",
    ("pro", "yearly"): "PADDLE_PRICE_PRO_YEARLY",
    ("max", "monthly"): "PADDLE_PRICE_MAX_MONTHLY",
    ("max", "yearly"): "PADDLE_PRICE_MAX_YEARLY",
}
# Paddle statuses that give access. past_due keeps access while Paddle
# retries the card; paused and canceled do not.
ACTIVE = {"active", "trialing", "past_due"}
SIGNATURE_TOLERANCE_S = 5 * 60


def prices() -> dict[str, str]:
    return {f"{plan}_{period}": setting(env) for (plan, period), env in PRICE_ENV.items()}


def plan_for_price(price_id: str) -> str | None:
    for (plan, _), env in PRICE_ENV.items():
        if price_id and setting(env) == price_id:
            return plan
    return None


def config() -> dict:
    token = setting("PADDLE_CLIENT_TOKEN")
    p = prices()
    return {
        "enabled": bool(token and all(p.values())),
        "environment": "sandbox" if setting("PADDLE_ENV") == "sandbox" else "production",
        "client_token": token,
        "prices": p,
    }


def verify_signature(raw: bytes, header: str, secret: str, now: float | None = None) -> bool:
    """Paddle-Signature: "ts=1671552777;h1=<hex>" — HMAC-SHA256 of "ts:body"."""
    try:
        parts = dict(kv.split("=", 1) for kv in header.split(";") if "=" in kv)
        ts = parts["ts"]
        sigs = [v for k, v in (kv.split("=", 1) for kv in header.split(";") if "=" in kv) if k == "h1"]
    except (KeyError, ValueError):
        return False
    if not sigs or not secret:
        return False
    if abs((now or time.time()) - int(ts)) > SIGNATURE_TOLERANCE_S:
        return False
    expected = hmac.new(secret.encode(), f"{ts}:".encode() + raw, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, s) for s in sigs)


class Billing:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        with self._db() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    paddle_id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    customer_id TEXT,
                    plan TEXT NOT NULL,
                    status TEXT NOT NULL,
                    price_id TEXT,
                    renews_at TEXT,
                    cancel_url TEXT,
                    update_url TEXT,
                    occurred_at TEXT,
                    updated REAL NOT NULL
                )""")

    def _db(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path, timeout=10)

    def apply_event(self, event: dict) -> bool:
        """Store a subscription.* event. Returns False when it is ignored."""
        kind = str(event.get("event_type", ""))
        if not kind.startswith("subscription."):
            return False
        data = event.get("data") or {}
        sub_id = data.get("id")
        user_id = (data.get("custom_data") or {}).get("user_id")
        items = data.get("items") or []
        price_id = ((items[0] if items else {}).get("price") or {}).get("id", "")
        plan = plan_for_price(price_id)
        if not sub_id or plan is None:
            return False
        occurred = str(event.get("occurred_at") or "")
        urls = data.get("management_urls") or {}
        with self._db() as db:
            row = db.execute("SELECT user_id, occurred_at FROM subscriptions WHERE paddle_id = ?", (sub_id,)).fetchone()
            if row and row[1] and occurred and occurred < row[1]:
                return False  # an older event arriving late: keep the newer state
            if user_id is None and row:
                user_id = row[0]
            if user_id is None:
                return False
            db.execute(
                """INSERT INTO subscriptions VALUES (?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(paddle_id) DO UPDATE SET user_id=excluded.user_id,
                     customer_id=excluded.customer_id, plan=excluded.plan, status=excluded.status,
                     price_id=excluded.price_id, renews_at=excluded.renews_at,
                     cancel_url=excluded.cancel_url, update_url=excluded.update_url,
                     occurred_at=excluded.occurred_at, updated=excluded.updated""",
                (sub_id, int(user_id), data.get("customer_id"), plan, str(data.get("status", "")), price_id,
                 (data.get("current_billing_period") or {}).get("ends_at") or data.get("next_billed_at"),
                 urls.get("cancel"), urls.get("update_payment_method"), occurred, time.time()))
        return True

    def plan_for(self, user_id: int | None) -> dict:
        free = {"plan": "free", "status": "none", "renews_at": None, "cancel_url": None, "update_url": None}
        if user_id is None:
            return free
        with self._db() as db:
            rows = db.execute(
                "SELECT plan, status, renews_at, cancel_url, update_url FROM subscriptions WHERE user_id = ? "
                "ORDER BY updated DESC", (user_id,)).fetchall()
        for plan, status, renews, cancel, update in rows:
            if status in ACTIVE:
                return {"plan": plan, "status": status, "renews_at": renews, "cancel_url": cancel, "update_url": update}
        return free


def install(app, data_dir: Path, user_for_token) -> Billing:
    """Routes: public config + webhook, and the signed-in user's plan."""
    billing = Billing(Path(data_dir) / "accounts.db")

    @app.get("/billing/config")
    def billing_config():
        return config()

    @app.post("/billing/paddle/webhook")
    async def paddle_webhook(request: Request):
        raw = await request.body()
        secret = os.environ.get("PADDLE_WEBHOOK_SECRET", "")
        if not verify_signature(raw, request.headers.get("paddle-signature", ""), secret):
            raise HTTPException(401, "bad signature")
        try:
            event = json.loads(raw)
        except ValueError as e:
            raise HTTPException(400, "not JSON") from e
        return {"ok": True, "stored": billing.apply_event(event)}

    @app.get("/billing/me")
    def billing_me(request: Request):
        auth = request.headers.get("authorization", "")
        token = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
        user = user_for_token(token)
        out = billing.plan_for(user["id"] if user else None)
        out["owner"] = user is None
        if out.get("renews_at"):
            try:
                out["renews_at"] = datetime.fromisoformat(out["renews_at"].replace("Z", "+00:00")).date().isoformat()
            except ValueError:
                pass
        return out

    return billing
