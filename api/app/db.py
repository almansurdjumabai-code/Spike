"""Storage for the SpikeClip web API: SQLite locally, Postgres in production.

DATABASE_URL picks the database:
    unset / sqlite:///path/to/file.db   SQLite (fine for development; on a
                                         host without a persistent disk the
                                         file is lost on every redeploy)
    postgres://… or postgresql://…      Postgres (recommended in production)

Queries are written once with "?" placeholders and work on both.

Schema
------
users          one row per website account
sessions       login sessions (only a SHA-256 of the token is stored)
licenses       one row per licence key (CLIP-XXXX-XXXX-XXXX)
activations    one row per (licence, device) the desktop app activated
paddle_events  ids of Paddle webhook events already processed (idempotency)
"""

from __future__ import annotations

import os
import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id {ID},
    email TEXT NOT NULL UNIQUE,              -- stored lower-case
    name TEXT NOT NULL,
    password TEXT NOT NULL,                  -- pbkdf2_sha256$rounds$salt$hash
    created_at BIGINT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at BIGINT NOT NULL
);
CREATE TABLE IF NOT EXISTS licenses (
    id {ID},
    license_key TEXT NOT NULL UNIQUE,        -- CLIP-XXXX-XXXX-XXXX
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    email TEXT,                              -- who it was issued to
    plan TEXT NOT NULL,                      -- pro | max
    status TEXT NOT NULL,                    -- active | past_due | paused | canceled | revoked
    max_activations INTEGER NOT NULL,
    expires_at BIGINT,                       -- NULL = no end date (manual / lifetime keys)
    source TEXT NOT NULL,                    -- paddle | manual
    paddle_subscription_id TEXT UNIQUE,
    paddle_customer_id TEXT,
    cancel_url TEXT,
    update_url TEXT,
    note TEXT,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,
    event_at TEXT                            -- occurred_at of the last Paddle event applied
);
CREATE INDEX IF NOT EXISTS licenses_user ON licenses(user_id);
CREATE TABLE IF NOT EXISTS activations (
    id {ID},
    license_id BIGINT NOT NULL REFERENCES licenses(id) ON DELETE CASCADE,
    device_hash TEXT NOT NULL,               -- SHA-256 of the app's device id
    device_name TEXT,
    platform TEXT,                           -- windows | macos | linux
    app_version TEXT,
    first_seen BIGINT NOT NULL,
    last_seen BIGINT NOT NULL,
    UNIQUE (license_id, device_hash)
);
CREATE TABLE IF NOT EXISTS paddle_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    received_at BIGINT NOT NULL
);
"""


class Database:
    def __init__(self, url: str | None = None):
        self.url = url if url is not None else os.environ.get("DATABASE_URL", "")
        self.postgres = self.url.startswith(("postgres://", "postgresql://"))
        self._lock = threading.Lock()
        if self.postgres:
            import psycopg  # noqa: F401  (imported here so SQLite needs nothing extra)
        else:
            path = self.url.removeprefix("sqlite:///") if self.url else "data/spikeclip-api.db"
            self.path = Path(path)
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()

    # -- connections ------------------------------------------------------
    @contextmanager
    def connect(self) -> Iterator[Conn]:
        if self.postgres:
            import psycopg

            conn = psycopg.connect(self.url)
            try:
                yield Conn(conn, postgres=True)
                conn.commit()
            except BaseException:
                conn.rollback()
                raise
            finally:
                conn.close()
        else:
            conn = sqlite3.connect(self.path, timeout=15)
            conn.execute("PRAGMA foreign_keys = ON")
            try:
                with self._lock:
                    yield Conn(conn, postgres=False)
                    conn.commit()
            except BaseException:
                conn.rollback()
                raise
            finally:
                conn.close()

    def init_schema(self) -> None:
        ddl = SCHEMA.replace("{ID}", "BIGSERIAL PRIMARY KEY" if self.postgres else "INTEGER PRIMARY KEY")
        with self.connect() as c:
            for stmt in (s.strip() for s in ddl.split(";")):
                if stmt:
                    c.execute(stmt)


class Conn:
    """One connection; "?" placeholders on both databases."""

    def __init__(self, raw: Any, postgres: bool):
        self.raw = raw
        self.postgres = postgres

    def _sql(self, sql: str) -> str:
        return sql.replace("?", "%s") if self.postgres else sql

    def execute(self, sql: str, params: tuple = ()) -> Any:
        cur = self.raw.cursor()
        cur.execute(self._sql(sql), params)
        return cur

    def one(self, sql: str, params: tuple = ()) -> tuple | None:
        return self.execute(sql, params).fetchone()

    def all(self, sql: str, params: tuple = ()) -> list[tuple]:
        return list(self.execute(sql, params).fetchall())

    def insert(self, sql: str, params: tuple = ()) -> int:
        """INSERT … and return the new row's id."""
        return int(self.execute(sql + " RETURNING id", params).fetchone()[0])
