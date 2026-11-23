"""Configuration of the SpikeClip web API (all from environment variables).

    DATABASE_URL              sqlite:///… (default data/spikeclip-api.db) or postgres://…
    ADMIN_TOKEN               owner token for /admin/* (SPIKECLIP_API_TOKEN also accepted)
    CORS_ORIGINS              comma-separated website origins (SPIKECLIP_CORS_ORIGINS also accepted)
    SIGNUP                    "open" (default) | "invite" | "closed"
    INVITE_CODE               required for SIGNUP=invite (SPIKECLIP_INVITE_CODE also accepted)

    WHOP_WEBHOOK_SECRET, WHOP_PRODUCTS, WHOP_CHECKOUT_*, BILLING_PROVIDER   Whop (see whop.py)
    PADDLE_ENV, PADDLE_CLIENT_TOKEN, PADDLE_WEBHOOK_SECRET,
    PADDLE_PRICE_{PRO,MAX}_{MONTHLY,YEARLY}   Paddle Billing (see paddle.py)

    DOWNLOAD_WINDOWS_URL, DOWNLOAD_MAC_URL, APP_VERSION   desktop builds for /downloads
                              (default: the latest release of the public spikeclip-releases
                              repo; set a variable to "off" to hide that build)
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


# What each paid plan unlocks in the desktop app. There is no free tier:
# without a valid key the app stays locked. The app enforces the limits on
# the user's PC; the API is the source of truth for which plan a key has.
# None means "no limit".
PLANS: dict[str, dict] = {
    "pro": {
        "label": "Pro",
        "max_activations": 1,
        "clips_per_month": None,
        "watermark": False,
        "max_resolution": 1080,
    },
    "max": {
        "label": "Max",
        "max_activations": 3,
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


# Installers are attached to releases of a public, files-only repository with
# fixed names, so "latest/download/<file>" always serves the newest build. The
# app itself is useless without a license key, so a public file is fine; the
# site still shows the buttons only to subscribers.
RELEASES = "https://github.com/almansurdjumabai-code/spikeclip-releases/releases/latest/download/"
DEFAULT_DOWNLOADS = {
    "windows": RELEASES + "SpikeClip-Setup.exe",
    "mac": RELEASES + "SpikeClip-mac-arm64.dmg",
}
APP_VERSION = "1.0.3"


def download_url(platform: str) -> str:
    """Where the installer lives; only licence holders are given it."""
    name = {"windows": "DOWNLOAD_WINDOWS_URL", "mac": "DOWNLOAD_MAC_URL"}.get(platform)
    if not name:
        return ""
    url = env(name, default=DEFAULT_DOWNLOADS[platform])
    return "" if url.lower() == "off" else url


def downloads() -> dict:
    """Public: which builds exist, never where they are."""
    return {
        "version": env("APP_VERSION", default=APP_VERSION),
        "windows": bool(download_url("windows")),
        "mac": bool(download_url("mac")),
        # Where the links point, without the links: the public releases repo or
        # custom DOWNLOAD_*_URL values set on the host.
        "source": "releases" if all(download_url(p) in ("", DEFAULT_DOWNLOADS[p]) for p in DEFAULT_DOWNLOADS) else "custom",
    }


# What a plan earns per month, by price, for the owner dashboard (USD).
MONTHLY_VALUE = {
    "PADDLE_PRICE_PRO_MONTHLY": 14.0,
    "PADDLE_PRICE_PRO_YEARLY": 11.0,
    "PADDLE_PRICE_MAX_MONTHLY": 29.0,
    "PADDLE_PRICE_MAX_YEARLY": 23.0,
}
