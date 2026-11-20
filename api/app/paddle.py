"""Paddle Billing: checkout config for the website, and webhooks that turn a
subscription into a licence key.

Paddle is the merchant of record (it charges, handles tax and refunds). Its
signed webhooks are the only thing that creates or changes a paid licence:

    subscription.created / activated / updated / past_due / paused /
    resumed / canceled      -> create the key on first sight, then keep
                               plan, status and expiry in step

The checkout passes customData.user_id, so the key lands in the buyer's
account. Webhook URL to register in Paddle: <api>/billing/paddle/webhook
"""

from __future__ import annotations

import hashlib
import hmac
import time
from datetime import datetime

from . import licenses
from .db import Conn
from .settings import env

# Public by design (sent to every browser that opens checkout); env vars of
# the same name override them. The webhook secret is NOT here.
DEFAULTS = {
    "PADDLE_ENV": "production",
    "PADDLE_CLIENT_TOKEN": "live_34e224b5ac701715da2f516291c",
    "PADDLE_PRICE_PRO_MONTHLY": "pri_01m7t5x5gssxg4xm7jr3t88j6v",
    "PADDLE_PRICE_PRO_YEARLY": "pri_01m7t62md9gyh9msbq36ycvrjq",
    "PADDLE_PRICE_MAX_MONTHLY": "pri_01m7t5y7dvkd5h42bgve5gh0r4",
    "PADDLE_PRICE_MAX_YEARLY": "pri_01m7t63qmhgx9m07pan3w0d4y3",
}
PRICE_ENV = {
    ("pro", "monthly"): "PADDLE_PRICE_PRO_MONTHLY",
    ("pro", "yearly"): "PADDLE_PRICE_PRO_YEARLY",
    ("max", "monthly"): "PADDLE_PRICE_MAX_MONTHLY",
    ("max", "yearly"): "PADDLE_PRICE_MAX_YEARLY",
}
SIGNATURE_TOLERANCE_S = 5 * 60


def setting(name: str) -> str:
    return env(name) or DEFAULTS.get(name, "")


def prices() -> dict[str, str]:
    return {f"{plan}_{period}": setting(name) for (plan, period), name in PRICE_ENV.items()}


def plan_for_price(price_id: str) -> str | None:
    for (plan, _), name in PRICE_ENV.items():
        if price_id and setting(name) == price_id:
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
    """Paddle-Signature: "ts=1671552777;h1=<hex>" = HMAC-SHA256 of "ts:body"."""
    pairs = [kv.split("=", 1) for kv in (header or "").split(";") if "=" in kv]
    ts = next((v for k, v in pairs if k == "ts"), None)
    sigs = [v for k, v in pairs if k == "h1"]
    if not ts or not sigs or not secret:
        return False
    try:
        if abs((now or time.time()) - int(ts)) > SIGNATURE_TOLERANCE_S:
            return False
    except ValueError:
        return False
    expected = hmac.new(secret.encode(), f"{ts}:".encode() + raw, hashlib.sha256).hexdigest()
    return any(hmac.compare_digest(expected, s) for s in sigs)


def _ts(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(datetime.fromisoformat(value).timestamp())
    except ValueError:
        return None


def apply_event(c: Conn, event: dict) -> str:
    """Apply one webhook event. Returns what happened, for the response/logs."""
    event_id = str(event.get("event_id") or "")
    kind = str(event.get("event_type") or "")
    if event_id:
        if c.one("SELECT 1 FROM paddle_events WHERE event_id = ?", (event_id,)):
            return "duplicate"
        c.execute("INSERT INTO paddle_events VALUES (?, ?, ?)", (event_id, kind, int(time.time())))
    if not kind.startswith("subscription."):
        return "ignored"

    data = event.get("data") or {}
    sub_id = data.get("id")
    items = data.get("items") or []
    price_id = ((items[0] if items else {}).get("price") or {}).get("id", "")
    plan = plan_for_price(price_id)
    if not sub_id or plan is None:
        return "ignored"
    occurred = str(event.get("occurred_at") or "")
    status = str(data.get("status") or "active")
    period_end = _ts((data.get("current_billing_period") or {}).get("ends_at")) or _ts(data.get("next_billed_at"))
    if status == "canceled":
        period_end = _ts(data.get("canceled_at")) or period_end or int(time.time())
    urls = data.get("management_urls") or {}

    row = c.one("SELECT id, event_at FROM licenses WHERE paddle_subscription_id = ?", (sub_id,))
    if row:
        if row[1] and occurred and occurred < row[1]:
            return "stale"  # an older event arriving late: keep the newer state
        c.execute(
            "UPDATE licenses SET plan = ?, status = ?, expires_at = ?, max_activations = ?, cancel_url = ?, "
            "update_url = ?, paddle_customer_id = COALESCE(?, paddle_customer_id), event_at = ?, updated_at = ? "
            "WHERE id = ?",
            (plan, status, period_end, _max_activations(plan), urls.get("cancel"), urls.get("update_payment_method"),
             data.get("customer_id"), occurred, int(time.time()), row[0]))
        return "updated"

    user_id = (data.get("custom_data") or {}).get("user_id")
    email = None
    if user_id is not None:
        u = c.one("SELECT email FROM users WHERE id = ?", (int(user_id),))
        email = u[0] if u else None
        if not u:
            user_id = None
    lic = licenses.issue(c, plan=plan, user_id=int(user_id) if user_id is not None else None, email=email,
                         source="paddle", expires_at=period_end, status=status, subscription_id=sub_id,
                         customer_id=data.get("customer_id"))
    c.execute("UPDATE licenses SET cancel_url = ?, update_url = ?, event_at = ? WHERE id = ?",
              (urls.get("cancel"), urls.get("update_payment_method"), occurred, lic["id"]))
    return "created"


def _max_activations(plan: str) -> int:
    from .settings import PLANS

    return PLANS[plan]["max_activations"]
