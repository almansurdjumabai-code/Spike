"""User accounts for the web app: sign up, log in, sessions.

Only active in a cloud deployment (SPIKECLIP_API_TOKEN set); the desktop app
never sees any of this.

Every account still shares ONE engine: one queue, one library. Until the
engine is made multi-tenant, sign-up is therefore closed unless an invite
code is configured:

    SPIKECLIP_INVITE_CODE   people who know it can create an account
    SPIKECLIP_OPEN_SIGNUP=1 anyone can (only for a private test)

Passwords are stored as PBKDF2-SHA256 hashes; session tokens are random and
stored only as SHA-256 hashes, so a copy of the database logs nobody in.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import threading
import time
from pathlib import Path

from fastapi import HTTPException, Request
from pydantic import BaseModel

PBKDF2_ROUNDS = 310_000
SESSION_DAYS = 30
EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,190}\.[^@\s]{2,}$")

_lock = threading.Lock()


class AccountError(ValueError):
    """A sign-up or log-in the user can fix; the message is shown to them."""


def signup_mode() -> str:
    if os.environ.get("SPIKECLIP_OPEN_SIGNUP") == "1":
        return "open"
    if os.environ.get("SPIKECLIP_INVITE_CODE"):
        return "invite"
    return "closed"


class Accounts:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    name TEXT NOT NULL,
                    password TEXT NOT NULL,
                    created REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    token_hash TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    expires REAL NOT NULL
                );
            """)
        self._cache: dict[str, float] = {}  # token hash -> expiry

    def _db(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.db_path, timeout=10)
        db.execute("PRAGMA foreign_keys = ON")
        return db

    # -- passwords ---------------------------------------------------------
    @staticmethod
    def _hash_password(password: str, salt: bytes | None = None) -> str:
        salt = salt or secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ROUNDS)
        return f"pbkdf2_sha256${PBKDF2_ROUNDS}${salt.hex()}${digest.hex()}"

    @staticmethod
    def _check_password(password: str, stored: str) -> bool:
        try:
            _, rounds, salt, digest = stored.split("$")
            got = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(rounds))
            return hmac.compare_digest(got.hex(), digest)
        except (ValueError, TypeError):
            return False

    # -- sessions ----------------------------------------------------------
    @staticmethod
    def _token_hash(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def _new_session(self, db: sqlite3.Connection, user_id: int) -> str:
        token = "sc_" + secrets.token_urlsafe(32)
        expires = time.time() + SESSION_DAYS * 86400
        db.execute("INSERT INTO sessions VALUES (?, ?, ?)", (self._token_hash(token), user_id, expires))
        return token

    def session_valid(self, token: str) -> bool:
        if not token.startswith("sc_"):
            return False
        h = self._token_hash(token)
        now = time.time()
        if self._cache.get(h, 0) > now:
            return True
        with self._db() as db:
            row = db.execute("SELECT expires FROM sessions WHERE token_hash = ?", (h,)).fetchone()
        if row and row[0] > now:
            self._cache[h] = min(row[0], now + 300)  # re-check the DB every 5 min
            return True
        self._cache.pop(h, None)
        return False

    def user_for(self, token: str) -> dict | None:
        with self._db() as db:
            row = db.execute(
                "SELECT u.id, u.email, u.name FROM sessions s JOIN users u ON u.id = s.user_id "
                "WHERE s.token_hash = ? AND s.expires > ?", (self._token_hash(token), time.time())).fetchone()
        return {"id": row[0], "email": row[1], "name": row[2]} if row else None

    def logout(self, token: str) -> None:
        h = self._token_hash(token)
        self._cache.pop(h, None)
        with self._db() as db:
            db.execute("DELETE FROM sessions WHERE token_hash = ?", (h,))

    # -- sign up / log in --------------------------------------------------
    def register(self, email: str, password: str, name: str, invite: str = "") -> tuple[str, dict]:
        mode = signup_mode()
        if mode == "closed":
            raise AccountError("Sign-up is closed right now.")
        if mode == "invite" and not hmac.compare_digest(
                invite.strip().encode(), os.environ["SPIKECLIP_INVITE_CODE"].encode()):
            raise AccountError("That invite code isn't valid.")
        email = (email or "").strip()
        name = (name or "").strip()[:60] or email.split("@")[0]
        if not EMAIL_RE.match(email):
            raise AccountError("Enter a valid email address.")
        if len(password or "") < 8:
            raise AccountError("Use at least 8 characters for the password.")
        with _lock, self._db() as db:
            try:
                cur = db.execute("INSERT INTO users (email, name, password, created) VALUES (?, ?, ?, ?)",
                                 (email, name, self._hash_password(password), time.time()))
            except sqlite3.IntegrityError:
                raise AccountError("An account with this email already exists. Log in instead.") from None
            token = self._new_session(db, cur.lastrowid)
        return token, {"id": cur.lastrowid, "email": email, "name": name}

    def login(self, email: str, password: str) -> tuple[str, dict]:
        with self._db() as db:
            row = db.execute("SELECT id, email, name, password FROM users WHERE email = ?",
                             ((email or "").strip(),)).fetchone()
            if not row or not self._check_password(password or "", row[3]):
                raise AccountError("Wrong email or password.")
            token = self._new_session(db, row[0])
        return token, {"id": row[0], "email": row[1], "name": row[2]}


class RegisterIn(BaseModel):
    email: str
    password: str
    name: str = ""
    invite: str = ""


class LoginIn(BaseModel):
    email: str
    password: str


def install(app, data_dir: Path) -> Accounts:
    """Routes for the web app's sign-up and log-in."""
    accounts = Accounts(Path(data_dir) / "accounts.db")

    def _bearer(request: Request) -> str:
        auth = request.headers.get("authorization", "")
        return auth[7:].strip() if auth.lower().startswith("bearer ") else ""

    @app.get("/auth/config")
    def auth_config():
        return {"signup": signup_mode()}

    @app.post("/auth/register")
    def register(body: RegisterIn):
        try:
            token, user = accounts.register(body.email, body.password, body.name, body.invite)
        except AccountError as e:
            raise HTTPException(400, str(e)) from e
        return {"token": token, "user": user}

    @app.post("/auth/login")
    def login(body: LoginIn):
        try:
            token, user = accounts.login(body.email, body.password)
        except AccountError as e:
            raise HTTPException(401, str(e)) from e
        return {"token": token, "user": user}

    @app.get("/auth/me")
    def me(request: Request):
        return {"user": accounts.user_for(_bearer(request))}

    @app.post("/auth/logout")
    def logout(request: Request):
        accounts.logout(_bearer(request))
        return {"ok": True}

    return accounts
