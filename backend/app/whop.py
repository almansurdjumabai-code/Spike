"""Whop: checkout links for the website, and webhooks that turn a Whop
membership into a licence key.

Whop charges the buyer and pays out to the seller. Its signed webhooks
(Standard Webhooks: webhook-id / webhook-timestamp / webhook-signature) are
the only thing that creates or changes a Whop licence:

    membership.activated / membership.updated  -> create the key on first
                                                  sight, keep it active
    membership.deactivated                      -> stop the key

A Whop buyer has no account on our site yet, so the key is stored with the
buyer's email; signing up or logging in with that email puts it in the
account (accounts.claim_licenses). While a membership is active the key has
no end date: Whop says when it stops, so a late renewal webhook can never
lock a paying customer out.

Webhook URL to register in Whop: <api>/billing/whop/webhook
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import time

from . import licenses
from .db import Conn
from .settings import env

# Public: product ids and checkout pages of the SpikeClip business on Whop.
# WHOP_PRODUCTS ("prod_a:pro,prod_b:max") and WHOP_CHECKOUT_* override them.
PRODUCTS = {
    "prod_o2igFfiAXZMKB": "pro",  # monthly
    "prod_NY3hBlI9G0KGI": "pro",  # annual
}
CHECKOUT = {
    "pro_monthly": "https://whop.com/spike-b252/gta-6-clip-earnings-platform",
    "pro_yearly": "https://whop.com/spike-b252/gta-6-clip-earnings-platform-annual-access",
    "max_monthly": "",
    "max_yearly": "",
}
# What each product earns per month, for the owner dashboard (USD).
MONTHLY_VALUE = {"prod_o2igFfiAXZMKB": 14.0, "prod_NY3hBlI9G0KGI": 11.0}
SIGNATURE_TOLERANCE_S = 5 * 60
ACTIVE = {"active", "trialing", "completed"}  # completed: a one-off purchase that stays valid


def products() -> dict[str, str]:
    out = dict(PRODUCTS)
    for pair in env("WHOP_PRODUCTS").split(","):
        if ":" in pair:
            pid, plan = (s.strip() for s in pair.split(":", 1))
            if pid and plan in ("pro", "max"):
                out[pid] = plan
    return out


def checkout() -> dict[str, str]:
    return {k: env(f"WHOP_CHECKOUT_{k.upper()}") or v for k, v in CHECKOUT.items()}


def config() -> dict:
    links = checkout()
    return {"enabled": bool(links["pro_monthly"] or links["pro_yearly"]), "checkout": links}


def _key(secret: str) -> bytes:
    # Standard Webhooks secrets look like "whsec_<base64>"; Whop has also handed
    # out plain strings that are used as-is.
    if secret.startswith("whsec_"):
        try:
            return base64.b64decode(secret[len("whsec_"):])
        except ValueError:
            pass
    return secret.encode()


def verify_signature(raw: bytes, headers, secret: str, now: float | None = None) -> bool:
    """HMAC-SHA256 over "id.timestamp.body", base64, sent as "v1,<sig>" (several, space-separated)."""
    msg_id = headers.get("webhook-id", "")
    ts = headers.get("webhook-timestamp", "")
    sigs = [s.split(",", 1)[1] for s in headers.get("webhook-signature", "").split() if s.startswith("v1,")]
    if not secret or not msg_id or not ts or not sigs:
        return False
    try:
        if abs((now or time.time()) - int(ts)) > SIGNATURE_TOLERANCE_S:
            return False
    except ValueError:
        return False
    signed = f"{msg_id}.{ts}.".encode() + raw
    expected = base64.b64encode(hmac.new(_key(secret), signed, hashlib.sha256).digest()).decode()
    return any(hmac.compare_digest(expected, s) for s in sigs)


def _email(data: dict) -> str | None:
    user = data.get("user") if isinstance(data.get("user"), dict) else {}
    email = data.get("email") or user.get("email") or ""
    email = str(email).strip().lower()
    return email or None


def _id(value) -> str:
    return str(value.get("id") if isinstance(value, dict) else value or "")


def apply_event(c: Conn, msg_id: str, event: dict) -> str:
    """Apply one webhook event. Returns what happened, for the response/logs."""
    kind = str(event.get("type") or event.get("action") or "")
    if msg_id:
        seen = f"whop:{msg_id}"
        if c.one("SELECT 1 FROM paddle_events WHERE event_id = ?", (seen,)):
            return "duplicate"
        c.execute("INSERT INTO paddle_events VALUES (?, ?, ?)", (seen, kind, int(time.time())))
    if not kind.startswith("membership."):
        return "ignored"

    data = event.get("data") or {}
    mem_id = _id(data)
    product = _id(data.get("product")) or _id(data.get("product_id"))
    plan = products().get(product)
    if not mem_id.startswith("mem_") or plan is None:
        return "ignored"
    status = str(data.get("status") or "")
    active = kind in ("membership.activated", "membership.went_valid") or (
        kind == "membership.updated" and status in ACTIVE)
    if kind in ("membership.deactivated", "membership.went_invalid") or (
            kind == "membership.updated" and status and status not in ACTIVE):
        active = False
    elif not active:
        return "ignored"

    sub = f"whop:{mem_id}"
    now = int(time.time())
    row = c.one("SELECT id FROM licenses WHERE paddle_subscription_id = ?", (sub,))
    if row:
        c.execute("UPDATE licenses SET plan = ?, status = ?, max_activations = ?, expires_at = ?, updated_at = ? "
                  "WHERE id = ?",
                  (plan, "active" if active else "canceled", _max_activations(plan), None if active else now,
                   now, row[0]))
        return "updated" if active else "stopped"
    if not active:
        return "ignored"  # deactivated before we ever saw it: nothing to stop

    email = _email(data)
    user = c.one("SELECT id FROM users WHERE email = ?", (email,)) if email else None
    lic = licenses.issue(c, plan=plan, user_id=user[0] if user else None, email=email, source="whop",
                         status="active", subscription_id=sub, customer_id=_id(data.get("user")) or None)
    c.execute("UPDATE licenses SET price_id = ? WHERE id = ?", (product, lic["id"]))
    return "created"


def _max_activations(plan: str) -> int:
    from .settings import PLANS

    return PLANS[plan]["max_activations"]
