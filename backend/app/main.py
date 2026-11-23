"""SpikeClip web API: accounts, payments and licence keys for the desktop app.

No video is processed, downloaded or stored here: clipping runs entirely on
the user's PC in the desktop app. This service only sells and checks keys.

Run locally:  uvicorn app.main:app --reload --port 8080   (from api/)
"""

from __future__ import annotations

import hmac
import json
import os
import time
from collections import defaultdict, deque

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from . import accounts, licenses, paddle, settings, whop
from .db import Database
from .status_page import STATUS_HTML

API_VERSION = 1


# ---------------------------------------------------------------- models
class RegisterIn(BaseModel):
    email: str
    password: str
    name: str = ""
    invite: str = ""


class LoginIn(BaseModel):
    email: str
    password: str


class LicenseIn(BaseModel):
    key: str = Field(..., max_length=40)
    device_id: str = Field(..., min_length=8, max_length=200)
    device_name: str = Field("", max_length=80)
    platform: str = Field("", max_length=20)
    app_version: str = Field("", max_length=20)


class IssueIn(BaseModel):
    plan: str
    email: str | None = None
    days: int | None = None  # None = no end date
    note: str | None = None


class RateLimiter:
    """Small in-memory limiter for the key endpoints (stops key guessing)."""

    def __init__(self, per_minute: int):
        self.per_minute = per_minute
        self.hits: dict[str, deque] = defaultdict(deque)

    def check(self, who: str) -> None:
        now = time.monotonic()
        q = self.hits[who]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= self.per_minute:
            raise HTTPException(429, "Too many attempts. Wait a minute and try again.")
        q.append(now)


def create_app(db: Database | None = None) -> FastAPI:
    db = db or Database()
    app = FastAPI(title="SpikeClip API", version=str(API_VERSION))
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins(),
                       allow_methods=["*"], allow_headers=["*"])
    key_limiter = RateLimiter(per_minute=int(os.environ.get("LICENSE_RATE_PER_MINUTE", "30")))

    def bearer(request: Request) -> str:
        auth = request.headers.get("authorization", "")
        return auth[7:].strip() if auth.lower().startswith("bearer ") else ""

    def is_admin(request: Request) -> bool:
        token, admin = bearer(request), settings.admin_token()
        return bool(admin) and hmac.compare_digest(token.encode(), admin.encode())

    def current_user(request: Request) -> dict | None:
        with db.connect() as c:
            return accounts.user_for_token(c, bearer(request))

    def require_user(request: Request) -> dict:
        user = current_user(request)
        if not user:
            raise HTTPException(401, "Log in first.")
        return user

    def require_admin(request: Request) -> None:
        if not is_admin(request):
            raise HTTPException(401, "Owner token required.")

    def client_ip(request: Request) -> str:
        fwd = request.headers.get("x-forwarded-for", "")
        return fwd.split(",")[0].strip() or (request.client.host if request.client else "?")

    # ---------------------------------------------------------- health
    @app.get("/health")
    def health():
        # `auth` tells the website that this API signs people in.
        # `db` says whether keys survive a restart: "postgres" yes, "sqlite" only on a persistent disk.
        return {"ok": True, "service": "spikeclip-api", "api_version": API_VERSION, "auth": True,
                "db": "postgres" if db.postgres else "sqlite"}

    # ---------------------------------------------------------- accounts
    @app.get("/auth/config")
    def auth_config():
        return {"signup": settings.signup_mode()}

    @app.post("/auth/register")
    def register(body: RegisterIn):
        try:
            with db.connect() as c:
                token, user = accounts.register(c, body.email, body.password, body.name, body.invite)
        except accounts.AccountError as e:
            raise HTTPException(400, str(e)) from e
        return {"token": token, "user": user}

    @app.post("/auth/login")
    def login(body: LoginIn):
        try:
            with db.connect() as c:
                token, user = accounts.login(c, body.email, body.password)
        except accounts.AccountError as e:
            raise HTTPException(401, str(e)) from e
        return {"token": token, "user": user}

    @app.get("/auth/me")
    def me(request: Request):
        return {"user": current_user(request), "owner": is_admin(request)}

    @app.get("/auth/check")
    def auth_check(request: Request):
        if not (is_admin(request) or current_user(request)):
            raise HTTPException(401, "Log in first.")
        return {"ok": True}

    @app.post("/auth/logout")
    def logout(request: Request):
        with db.connect() as c:
            accounts.logout(c, bearer(request))
        return {"ok": True}

    # ---------------------------------------------------------- billing
    @app.get("/billing/config")
    def billing_config():
        # provider: which checkout the website opens. Whop when its links are set.
        cfg = paddle.config()
        cfg["whop"] = whop.config()
        cfg["provider"] = settings.env("BILLING_PROVIDER") or ("whop" if cfg["whop"]["enabled"] else "paddle")
        return cfg

    @app.post("/billing/whop/webhook")
    async def whop_webhook(request: Request):
        raw = await request.body()
        if not whop.verify_signature(raw, request.headers, settings.env("WHOP_WEBHOOK_SECRET")):
            raise HTTPException(401, "bad signature")
        try:
            event = json.loads(raw)
        except ValueError as e:
            raise HTTPException(400, "not JSON") from e
        with db.connect() as c:
            result = whop.apply_event(c, request.headers.get("webhook-id", ""), event)
        return {"ok": True, "result": result}

    @app.post("/billing/paddle/webhook")
    async def paddle_webhook(request: Request):
        raw = await request.body()
        secret = settings.env("PADDLE_WEBHOOK_SECRET")
        if not paddle.verify_signature(raw, request.headers.get("paddle-signature", ""), secret):
            raise HTTPException(401, "bad signature")
        try:
            event = json.loads(raw)
        except ValueError as e:
            raise HTTPException(400, "not JSON") from e
        with db.connect() as c:
            result = paddle.apply_event(c, event)
        return {"ok": True, "result": result}

    @app.get("/billing/me")
    def billing_me(request: Request):
        user = current_user(request)
        with db.connect() as c:
            plan = licenses.best_plan(c, user["id"] if user else None)
            lic = next((x for x in licenses.for_user(c, user["id"]) if x["plan"] == plan), None) if user else None
        return {
            "plan": plan,
            "status": lic["status"] if lic else "none",
            "renews_at": licenses.iso(lic["expires_at"])[:10] if lic and lic["expires_at"] else None,
            "cancel_url": lic.get("cancel_url") if lic else None,
            "update_url": lic.get("update_url") if lic else None,
            "owner": is_admin(request) and not user,
        }

    # ---------------------------------------------------------- account page
    @app.get("/licenses/me")
    def my_licenses(user: dict = Depends(require_user)):
        with db.connect() as c:
            return {"licenses": [licenses.public(c, lic) for lic in licenses.for_user(c, user["id"])]}

    @app.delete("/licenses/{key}/devices/{device}")
    def release_device(key: str, device: str, user: dict = Depends(require_user)):
        with db.connect() as c:
            lic = licenses.get(c, key)
            if not lic or lic["user_id"] != user["id"]:
                raise HTTPException(404, "No such license in your account.")
            if not licenses.remove_device(c, lic["id"], device):
                raise HTTPException(404, "No such device on this license.")
            return licenses.public(c, licenses.get(c, key))

    # ---------------------------------------------------------- desktop app
    @app.post("/v1/license/activate")
    def activate(body: LicenseIn, request: Request):
        key_limiter.check(client_ip(request))
        with db.connect() as c:
            return licenses.activate(c, body.key, body.device_id, body.device_name, body.platform, body.app_version)

    @app.post("/v1/license/validate")
    def validate(body: LicenseIn, request: Request):
        key_limiter.check(client_ip(request))
        with db.connect() as c:
            return licenses.validate(c, body.key, body.device_id, body.app_version)

    @app.post("/v1/license/deactivate")
    def deactivate(body: LicenseIn, request: Request):
        key_limiter.check(client_ip(request))
        with db.connect() as c:
            return licenses.deactivate(c, body.key, body.device_id)

    @app.get("/v1/plans")
    def plans():
        return {"plans": settings.PLANS}

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def status_page():
        return STATUS_HTML

    @app.get("/downloads")
    def downloads():
        return settings.downloads()

    @app.get("/downloads/{platform}")
    def download_link(platform: str, user: dict = Depends(require_user)):
        """The installer link, for licence holders only."""
        if platform not in ("windows", "mac"):
            raise HTTPException(404, "Unknown platform.")
        with db.connect() as c:
            active = any(licenses.state(lic) == "ok" for lic in licenses.for_user(c, user["id"]))
        if not active:
            raise HTTPException(403, "Downloads are for SpikeClip subscribers. Get Pro to download the app.")
        url = settings.download_url(platform)
        if not url:
            raise HTTPException(404, "This build isn't available yet.")
        return {"url": url, "version": settings.downloads()["version"]}

    # ---------------------------------------------------------- owner
    @app.post("/admin/licenses", dependencies=[Depends(require_admin)])
    def admin_issue(body: IssueIn):
        email = (body.email or "").strip().lower() or None
        with db.connect() as c:
            user = c.one("SELECT id FROM users WHERE email = ?", (email,)) if email else None
            try:
                lic = licenses.issue(c, plan=body.plan, user_id=user[0] if user else None, email=email,
                                     source="manual", note=body.note,
                                     expires_at=int(time.time()) + body.days * 86400 if body.days else None)
            except ValueError as e:
                raise HTTPException(400, str(e)) from e
            return licenses.public(c, lic)

    @app.get("/admin/licenses", dependencies=[Depends(require_admin)])
    def admin_list(limit: int = 100):
        with db.connect() as c:
            rows = c.all(f"SELECT {licenses.COLUMNS} FROM licenses ORDER BY created_at DESC LIMIT ?", (min(limit, 500),))
            return {"licenses": [dict(licenses.public(c, licenses._row(r)), email=r[3], source=r[8]) for r in rows]}

    @app.get("/admin/stats", dependencies=[Depends(require_admin)])
    def admin_stats():
        now = int(time.time())
        with db.connect() as c:
            users = c.one("SELECT COUNT(*) FROM users")[0]
            rows = c.all(f"SELECT {licenses.COLUMNS}, price_id FROM licenses")
            activations = c.one("SELECT COUNT(*) FROM activations")[0]
            new_week = c.one("SELECT COUNT(*) FROM users WHERE created_at > ?", (now - 7 * 86400,))[0]
        value = {paddle.setting(k): v for k, v in settings.MONTHLY_VALUE.items()} | whop.MONTHLY_VALUE
        active = [r for r in rows if licenses.state(licenses._row(r[:-1]), now) == "ok"]
        paid = [r for r in active if r[8] in ("paddle", "whop")]
        mrr = sum(value.get(r[-1], 0.0) for r in paid)
        return {
            "users": users,
            "users_last_7_days": new_week,
            "licenses_total": len(rows),
            "licenses_active": len(active),
            "paid_active": len(paid),
            "by_plan": {p: sum(1 for r in active if r[4] == p) for p in settings.PLANS},
            "activations": activations,
            "mrr_usd": round(mrr, 2),
        }

    @app.get("/admin/users", dependencies=[Depends(require_admin)])
    def admin_users(limit: int = 100):
        with db.connect() as c:
            rows = c.all("SELECT id, email, name, created_at FROM users ORDER BY created_at DESC LIMIT ?",
                         (min(limit, 500),))
            return {"users": [{"id": r[0], "email": r[1], "name": r[2], "created_at": licenses.iso(r[3]),
                               "plan": licenses.best_plan(c, r[0])} for r in rows]}

    @app.post("/admin/licenses/{key}/revoke", dependencies=[Depends(require_admin)])
    def admin_revoke(key: str):
        with db.connect() as c:
            lic = licenses.get(c, key)
            if not lic:
                raise HTTPException(404, "No such license.")
            c.execute("UPDATE licenses SET status = 'revoked', updated_at = ? WHERE id = ?", (int(time.time()), lic["id"]))
            return licenses.public(c, licenses.get(c, key))

    return app


app = create_app() if os.environ.get("SPIKECLIP_API_NO_AUTOAPP") != "1" else None
