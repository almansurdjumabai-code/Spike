"""Configuration of the SpikeClip web API (all from environment variables).

    DATABASE_URL              sqlite:///… (default data/spikeclip-api.db) or postgres://…
    ADMIN_TOKEN               owner token for /admin/* (SPIKECLIP_API_TOKEN also accepted)
    CORS_ORIGINS              comma-separated website origins (SPIKECLIP_CORS_ORIGINS also accepted)
    SIGNUP                    "open" (default) | "invite" | "closed"
    INVITE_CODE               required for SIGNUP=invite (SPIKECLIP_INVITE_CODE also accepted)

    PADDLE_ENV, PADDLE_CLIENT_TOKEN, PADDLE_WEBHOOK_SECRET,
    PADDLE_PRICE_{PRO,MAX}_{MONTHLY,YEARLY}   Paddle Billing (see paddle.py)

    DOWNLOAD_WINDOWS_URL, DOWNLOAD_MAC_URL, APP_VERSION   desktop builds for /downloads
"""

from __future__ import annotations

import os


def env(*names: str, default: str = "") -> str:
    for n in names:
        v = os.environ.get(n)
        if v:
            return v
    return default


def admin_token() -> str:
    return env("ADMIN_TOKEN", "SPIKECLIP_API_TOKEN")


def cors_origins() -> list[str]:
    raw = env("CORS_ORIGINS", "SPIKECLIP_CORS_ORIGINS")
    local = ["http://localhost:5173", "http://127.0.0.1:5173"]
    return local + [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]


def signup_mode() -> str:
    mode = env("SIGNUP", default="open").lower()
    if os.environ.get("SPIKECLIP_OPEN_SIGNUP") == "1":
        return "open"
    if mode == "invite" and not invite_code():
        return "closed"
    return mode if mode in ("open", "invite", "closed") else "open"


def invite_code() -> str:
    return env("INVITE_CODE", "SPIKECLIP_INVITE_CODE")


# What each plan unlocks in the desktop app. The app enforces the limits on
# the user's PC; the API is the source of truth for which plan a key has.
# None means "no limit".
PLANS: dict[str, dict] = {
    "free": {
        "label": "Free trial",
        "max_activations": 1,
        "clips_per_month": 5,
        "watermark": True,
        "max_resolution": 720,
    },
    "pro": {
        "label": "Pro",
        "max_activations": 2,
        "clips_per_month": None,
        "watermark": False,
        "max_resolution": 1080,
    },
    "max": {
        "label": "Max",
        "max_activations": 5,
        "clips_per_month": None,
        "watermark": False,
        "max_resolution": 2160,
    },
}

# How the desktop app should behave between checks.
CHECK_AGAIN_AFTER_HOURS = 72
OFFLINE_GRACE_DAYS = 7
# A subscription key keeps working this long past the paid period, so a
# renewal that is a few hours late doesn't lock anyone out.
RENEWAL_GRACE_SECONDS = 3 * 86400


def downloads() -> dict:
    return {
        "version": env("APP_VERSION", default="2.1.0"),
        "windows": env("DOWNLOAD_WINDOWS_URL") or None,
        "mac": env("DOWNLOAD_MAC_URL") or None,
    }
