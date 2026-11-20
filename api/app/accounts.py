"""Website accounts: sign up, log in, sessions. Passwords are PBKDF2-SHA256;
session tokens are random and stored only as a SHA-256 hash."""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import time

from . import settings
from .db import Conn

PBKDF2_ROUNDS = 310_000
SESSION_DAYS = 30
EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,190}\.[^@\s]{2,}$")


class AccountError(ValueError):
    """Something the visitor can fix; the message is shown to them."""


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ROUNDS)
    return f"pbkdf2_sha256${PBKDF2_ROUNDS}${salt.hex()}${digest.hex()}"


def check_password(password: str, stored: str) -> bool:
    try:
        _, rounds, salt, digest = stored.split("$")
        got = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(rounds))
        return hmac.compare_digest(got.hex(), digest)
    except (ValueError, TypeError):
        return False


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_session(c: Conn, user_id: int) -> str:
    token = "sc_" + secrets.token_urlsafe(32)
    c.execute("INSERT INTO sessions VALUES (?, ?, ?)", (token_hash(token), user_id, int(time.time()) + SESSION_DAYS * 86400))
    return token


def user_dict(row: tuple) -> dict:
    return {"id": row[0], "email": row[1], "name": row[2]}


def register(c: Conn, email: str, password: str, name: str, invite: str = "") -> tuple[str, dict]:
    mode = settings.signup_mode()
    if mode == "closed":
        raise AccountError("Sign-up is closed right now.")
    if mode == "invite" and not hmac.compare_digest(invite.strip().encode(), settings.invite_code().encode()):
        raise AccountError("That invite code isn't valid.")
    email = (email or "").strip().lower()
    name = (name or "").strip()[:60] or email.split("@")[0]
    if not EMAIL_RE.match(email):
        raise AccountError("Enter a valid email address.")
    if len(password or "") < 8:
        raise AccountError("Use at least 8 characters for the password.")
    if c.one("SELECT 1 FROM users WHERE email = ?", (email,)):
        raise AccountError("An account with this email already exists. Log in instead.")
    uid = c.insert("INSERT INTO users (email, name, password, created_at) VALUES (?, ?, ?, ?)",
                   (email, name, hash_password(password), int(time.time())))
    return new_session(c, uid), {"id": uid, "email": email, "name": name}


def login(c: Conn, email: str, password: str) -> tuple[str, dict]:
    row = c.one("SELECT id, email, name, password FROM users WHERE email = ?", ((email or "").strip().lower(),))
    if not row or not check_password(password or "", row[3]):
        raise AccountError("Wrong email or password.")
    return new_session(c, row[0]), user_dict(row)


def user_for_token(c: Conn, token: str) -> dict | None:
    if not token or not token.startswith("sc_"):
        return None
    row = c.one(
        "SELECT u.id, u.email, u.name FROM sessions s JOIN users u ON u.id = s.user_id "
        "WHERE s.token_hash = ? AND s.expires_at > ?", (token_hash(token), int(time.time())))
    return user_dict(row) if row else None


def logout(c: Conn, token: str) -> None:
    c.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash(token),))
