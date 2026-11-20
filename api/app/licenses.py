"""Licence keys and device activations.

A key looks like CLIP-7K3M-Q9XW-2HPD: 12 characters from an alphabet
without look-alikes (no 0/O, 1/I/L), ~59 bits of randomness.

The desktop app talks to three calls:
    activate    first run on a device: binds the device to the key
    validate    every few days: is this key still good on this device?
    deactivate  frees the device's slot (e.g. before moving to a new PC)

Every answer has a machine-readable `code` and a human `message`:
    ok, invalid_key, revoked, expired, inactive, activation_limit, not_activated
"""

from __future__ import annotations

import hashlib
import re
import secrets
import time
from datetime import UTC, datetime

from . import settings
from .db import Conn

ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
KEY_RE = re.compile(r"^CLIP-[0-9A-Z]{4}-[0-9A-Z]{4}-[0-9A-Z]{4}$")
USABLE = ("active", "past_due")  # past_due: Paddle is retrying the card, keep working

MESSAGES = {
    "ok": "License is active.",
    "invalid_key": "This license key doesn't exist. Check it for typos.",
    "revoked": "This license key has been revoked. Contact support.",
    "expired": "This license has expired. Renew your plan to keep using SpikeClip.",
    "inactive": "This subscription is paused or cancelled. Renew it to keep using SpikeClip.",
    "activation_limit": "This key is already active on the maximum number of devices. "
                        "Deactivate one from your account page, then try again.",
    "not_activated": "This device isn't activated for this key yet.",
}

COLUMNS = ("id, license_key, user_id, email, plan, status, max_activations, expires_at, source, "
           "paddle_subscription_id, cancel_url, update_url, created_at")


def new_key() -> str:
    chars = "".join(secrets.choice(ALPHABET) for _ in range(12))
    return f"CLIP-{chars[:4]}-{chars[4:8]}-{chars[8:]}"


def normalize_key(key: str) -> str:
    k = re.sub(r"[^0-9A-Za-z]", "", key or "").upper()
    k = k.removeprefix("CLIP")
    return f"CLIP-{k[:4]}-{k[4:8]}-{k[8:12]}" if len(k) == 12 else ""


def device_hash(device_id: str) -> str:
    return hashlib.sha256(("spikeclip-device:" + (device_id or "")).encode()).hexdigest()


def iso(ts: int | None) -> str | None:
    return datetime.fromtimestamp(ts, UTC).isoformat().replace("+00:00", "Z") if ts else None


def _row(row: tuple) -> dict:
    keys = [k.strip() for k in COLUMNS.split(",")]
    return dict(zip(keys, row))


def issue(c: Conn, *, plan: str, user_id: int | None, email: str | None, source: str,
          expires_at: int | None = None, status: str = "active", subscription_id: str | None = None,
          customer_id: str | None = None, note: str | None = None) -> dict:
    if plan not in settings.PLANS:
        raise ValueError(f"unknown plan {plan!r}")
    now = int(time.time())
    for _ in range(5):  # a collision is astronomically unlikely; retry anyway
        key = new_key()
        if not c.one("SELECT 1 FROM licenses WHERE license_key = ?", (key,)):
            break
    lid = c.insert(
        "INSERT INTO licenses (license_key, user_id, email, plan, status, max_activations, expires_at, source, "
        "paddle_subscription_id, paddle_customer_id, note, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (key, user_id, email, plan, status, settings.PLANS[plan]["max_activations"], expires_at, source,
         subscription_id, customer_id, note, now, now))
    return get_by_id(c, lid)


def get_by_id(c: Conn, lid: int) -> dict:
    return _row(c.one(f"SELECT {COLUMNS} FROM licenses WHERE id = ?", (lid,)))


def get(c: Conn, key: str) -> dict | None:
    row = c.one(f"SELECT {COLUMNS} FROM licenses WHERE license_key = ?", (normalize_key(key),))
    return _row(row) if row else None


def state(lic: dict, now: int | None = None) -> str:
    """ok / revoked / expired / inactive for a licence, ignoring devices."""
    now = now or int(time.time())
    if lic["status"] == "revoked":
        return "revoked"
    if lic["expires_at"] and lic["expires_at"] + (settings.RENEWAL_GRACE_SECONDS if lic["source"] == "paddle" else 0) < now:
        return "expired"
    if lic["status"] not in USABLE:
        return "inactive"
    return "ok"


def activations(c: Conn, lid: int) -> list[dict]:
    rows = c.all("SELECT device_hash, device_name, platform, app_version, first_seen, last_seen "
                 "FROM activations WHERE license_id = ? ORDER BY first_seen", (lid,))
    return [{"device": r[0][:16], "name": r[1], "platform": r[2], "app_version": r[3],
             "first_seen": iso(r[4]), "last_seen": iso(r[5])} for r in rows]


def public(c: Conn, lic: dict) -> dict:
    """What the desktop app and the account page see about a licence."""
    plan = settings.PLANS[lic["plan"]]
    devices = activations(c, lic["id"])
    return {
        "key": lic["license_key"],
        "plan": lic["plan"],
        "plan_label": plan["label"],
        "status": lic["status"],
        "state": state(lic),
        "expires_at": iso(lic["expires_at"]),
        "max_activations": lic["max_activations"],
        "activations_used": len(devices),
        "devices": devices,
        "features": {k: v for k, v in plan.items() if k not in ("label", "max_activations")},
        "manage": {"cancel_url": lic.get("cancel_url"), "update_url": lic.get("update_url")},
    }


def _answer(c: Conn, code: str, lic: dict | None = None) -> dict:
    out = {"ok": code == "ok", "code": code, "message": MESSAGES[code],
           "check_again_after_hours": settings.CHECK_AGAIN_AFTER_HOURS,
           "offline_grace_days": settings.OFFLINE_GRACE_DAYS,
           "server_time": iso(int(time.time()))}
    if lic is not None:
        out["license"] = public(c, lic)
    return out


def activate(c: Conn, key: str, device_id: str, device_name: str = "", platform: str = "",
             app_version: str = "") -> dict:
    lic = get(c, key)
    if not lic:
        return _answer(c, "invalid_key")
    st = state(lic)
    if st != "ok":
        return _answer(c, st, lic)
    now = int(time.time())
    dh = device_hash(device_id)
    if c.one("SELECT 1 FROM activations WHERE license_id = ? AND device_hash = ?", (lic["id"], dh)):
        c.execute("UPDATE activations SET last_seen = ?, device_name = ?, platform = ?, app_version = ? "
                  "WHERE license_id = ? AND device_hash = ?",
                  (now, device_name[:80], platform[:20], app_version[:20], lic["id"], dh))
        return _answer(c, "ok", lic)
    used = c.one("SELECT COUNT(*) FROM activations WHERE license_id = ?", (lic["id"],))[0]
    if used >= lic["max_activations"]:
        return _answer(c, "activation_limit", lic)
    c.execute("INSERT INTO activations (license_id, device_hash, device_name, platform, app_version, first_seen, last_seen) "
              "VALUES (?, ?, ?, ?, ?, ?, ?)", (lic["id"], dh, device_name[:80], platform[:20], app_version[:20], now, now))
    return _answer(c, "ok", lic)


def validate(c: Conn, key: str, device_id: str, app_version: str = "") -> dict:
    lic = get(c, key)
    if not lic:
        return _answer(c, "invalid_key")
    dh = device_hash(device_id)
    if not c.one("SELECT 1 FROM activations WHERE license_id = ? AND device_hash = ?", (lic["id"], dh)):
        return _answer(c, "not_activated", lic)
    st = state(lic)
    if st == "ok":
        c.execute("UPDATE activations SET last_seen = ?, app_version = COALESCE(NULLIF(?, ''), app_version) "
                  "WHERE license_id = ? AND device_hash = ?", (int(time.time()), app_version[:20], lic["id"], dh))
    return _answer(c, st, lic)


def deactivate(c: Conn, key: str, device_id: str) -> dict:
    lic = get(c, key)
    if not lic:
        return _answer(c, "invalid_key")
    c.execute("DELETE FROM activations WHERE license_id = ? AND device_hash = ?", (lic["id"], device_hash(device_id)))
    return {"ok": True, "code": "deactivated", "message": "This device was released from the key."}


def remove_device(c: Conn, lid: int, device_prefix: str) -> bool:
    """Account page: release a device by the short id shown there."""
    rows = c.all("SELECT device_hash FROM activations WHERE license_id = ?", (lid,))
    match = [r[0] for r in rows if r[0].startswith(device_prefix) and len(device_prefix) >= 8]
    for h in match:
        c.execute("DELETE FROM activations WHERE license_id = ? AND device_hash = ?", (lid, h))
    return bool(match)


def for_user(c: Conn, user_id: int) -> list[dict]:
    rows = c.all(f"SELECT {COLUMNS} FROM licenses WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    return [_row(r) for r in rows]


def best_plan(c: Conn, user_id: int | None) -> str:
    if user_id is None:
        return "none"
    rank = {"none": 0, "pro": 1, "max": 2}
    best = "none"
    for lic in for_user(c, user_id):
        if state(lic) == "ok" and rank[lic["plan"]] > rank[best]:
            best = lic["plan"]
    return best
