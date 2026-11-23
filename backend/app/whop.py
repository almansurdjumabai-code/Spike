"""Whop: checkout links for the website, and webhooks that turn a Whop
membership into a licence key.

Whop charges the buyer and pays out to the seller. Its signed webhooks
(Standard Webhooks: webhook-id / webhook-timestamp / webhook-signature) are
the only thing that creates or changes a Whop licence:

    membership.activated / membership.updated  -> create the key on first
                                                  sight, keep it active
    membership.deactivated                      -> stop the key
    payment.succeeded                           -> same as activated (for webhooks
                                                  that only subscribe to payments)
    payment.refunded / refund.created           -> stop the key

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
    # webhook_ready: the secret is set, so paid memberships can turn into keys (never the secret itself).
    return {"enabled": bool(links["pro_monthly"] or links["pro_yearly"]), "checkout": links,
            "webhook_ready": bool(env("WHOP_WEBHOOK_SECRET"))}


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


def _find(obj, test, depth: int = 0):
    """First value anywhere in the payload (depth-first) that passes test(key, value)."""
    if depth > 6:
        return None
    if isinstance(obj, dict):
        for k, v in obj.items():
            if test(k, v):
                return v
        for v in obj.values():
            hit = _find(v, test, depth + 1)
            if hit is not None:
                return hit
    elif isinstance(obj, list):
        for v in obj:
            hit = _find(v, test, depth + 1)
            if hit is not None:
                return hit
    return None


def _str_id(prefix: str):
    return lambda k, v: isinstance(v, str) and v.startswith(prefix) and k in ("id", f"{prefix[:-1]}_id",
                                                                             "membership_id", "product_id",
                                                                             "membership", "product")


def _email(data: dict) -> str | None:
    # Whop's payment payload has "customer_email"; membership payloads nest "email" under user.
    email = _find(data, lambda k, v: k in ("customer_email", "email", "user_email") and isinstance(v, str) and "@" in v)
    return str(email).strip().lower() if email else None


def _id(value) -> str:
    return str(value.get("id") if isinstance(value, dict) else value or "")


START = ("membership.activated", "membership.went_valid", "payment.succeeded")
STOP = ("membership.deactivated", "membership.went_invalid", "payment.refunded", "refund.created")


def apply_event(c: Conn, msg_id: str, event: dict) -> str:
    """Apply one webhook event. Returns what happened, for the response/logs.

    Whop sends either membership events or payment events, depending on what the
    webhook subscribes to, so both are understood: the membership id, product id
    and buyer email are looked up wherever they sit in the payload.
    """
    kind = str(event.get("type") or event.get("action") or "")
    data = event.get("data") or {}
    seen = f"whop:{msg_id}" if msg_id else ""
    already = bool(seen and c.one("SELECT 1 FROM paddle_events WHERE event_id = ?", (seen,)))
    if already:
        # A replay may still fill in a buyer email the first pass missed...
        if _backfill(c, data):
            return "duplicate (email linked)"
        # ...and an event an older version marked as seen without making the key
        # (e.g. it skipped payment events) is applied now.
        mem_id = _membership(data)
        if not mem_id or c.one("SELECT 1 FROM licenses WHERE paddle_subscription_id = ?", (f"whop:{mem_id}",)):
            return "duplicate"
    result = _apply(c, kind, data)
    # Only remember events that changed something, so a replay after a fix still works.
    if seen and not already and result not in ("ignored",):
        c.execute("INSERT INTO paddle_events VALUES (?, ?, ?)", (seen, kind, int(time.time())))
    return result


def _membership(data: dict) -> str:
    return _id(data) if _id(data).startswith("mem_") else str(_find(data, _str_id("mem_")) or "")


def _backfill(c: Conn, data: dict) -> bool:
    """Give an email-less Whop key the buyer's email, and their account if one exists."""
    mem_id, email = _membership(data), _email(data)
    if not mem_id.startswith("mem_") or not email:
        return False
    row = c.one("SELECT id FROM licenses WHERE paddle_subscription_id = ? AND email IS NULL", (f"whop:{mem_id}",))
    if not row:
        return False
    user = c.one("SELECT id FROM users WHERE email = ?", (email,))
    c.execute("UPDATE licenses SET email = ?, user_id = COALESCE(user_id, ?), updated_at = ? WHERE id = ?",
              (email, user[0] if user else None, int(time.time()), row[0]))
    return True


def _apply(c: Conn, kind: str, data: dict) -> str:
    if not kind.startswith(("membership.", "payment.", "refund.")):
        return "ignored"
    mem_id = _membership(data)
    product = str(_find(data, _str_id("prod_")) or "")
    # Only our own Whop company can sign these webhooks, so any of its products is
    # SpikeClip: Pro unless WHOP_PRODUCTS maps it to another plan.
    plan = products().get(product, "pro")
    if not mem_id.startswith("mem_"):
        return "ignored"
    status = str(data.get("status") or "")
    if kind in STOP or (kind == "membership.updated" and status and status not in ACTIVE):
        active = False
    elif kind in START or (kind == "membership.updated" and status in ACTIVE):
        active = True
    else:
        return "ignored"  # payment.failed, payment.pending and the like

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
        return "ignored"  # stopped before we ever saw it: nothing to stop

    email = _email(data)
    user = c.one("SELECT id FROM users WHERE email = ?", (email,)) if email else None
    whop_user = _find(data, _str_id("user_"))
    lic = licenses.issue(c, plan=plan, user_id=user[0] if user else None, email=email, source="whop",
                         status="active", subscription_id=sub, customer_id=str(whop_user) if whop_user else None)
    c.execute("UPDATE licenses SET price_id = ? WHERE id = ?", (product, lic["id"]))
    return "created"


def _max_activations(plan: str) -> int:
    from .settings import PLANS

    return PLANS[plan]["max_activations"]
