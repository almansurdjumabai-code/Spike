"""Cloud deployment settings for the API: who may call it and from where.

On a desktop the engine listens on 127.0.0.1 and nothing else can reach it,
so it needs no authentication. Deployed to a server, the same API is on the
internet, and it reads and writes video files and holds the user's provider
keys. Everything here is driven by environment variables and is a no-op when
none of them is set, so the desktop app behaves exactly as before.

    SPIKECLIP_API_TOKEN        shared secret; when set, every request needs it
    SPIKECLIP_CORS_ORIGINS     comma-separated origins of the web frontend,
                               e.g. https://app.spikeclip.example
    SPIKECLIP_ALLOWED_HOSTS    comma-separated Host names the API answers to,
                               e.g. api.spikeclip.example ("*" for any).
                               On Render, RENDER_EXTERNAL_HOSTNAME (set by the
                               platform: the service's *.onrender.com name) is
                               added automatically.
    SPIKECLIP_INSECURE_NO_AUTH set to 1 to allow binding a public interface
                               without a token (local Docker only)

The token is accepted as `Authorization: Bearer <token>`, as an
`X-SpikeClip-Token` header, or as an `access_token` query parameter. The query
form exists because <img>, <video> and WebSocket requests cannot carry
headers; prefer the header everywhere else, since URLs end up in logs.
"""

from __future__ import annotations

import hmac
import os
from urllib.parse import parse_qs

TOKEN_ENV = "SPIKECLIP_API_TOKEN"
TOKEN_HEADER = b"x-spikeclip-token"
TOKEN_QUERY = "access_token"

LOCAL_HOSTS = ["127.0.0.1", "localhost"]
LOCAL_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]  # Vite dev server

# Reachable without the token: the health probe the frontend uses to find out
# whether it needs to ask for one, and OAuth redirects a provider sends the
# browser back to (those carry their own single-use state).
PUBLIC_PATHS = ("/health",)


def _csv(name: str) -> list[str]:
    return [v.strip().rstrip("/") for v in os.environ.get(name, "").split(",") if v.strip()]


def api_token() -> str | None:
    return os.environ.get(TOKEN_ENV) or None


def cors_origins() -> list[str]:
    return LOCAL_ORIGINS + _csv("SPIKECLIP_CORS_ORIGINS")


def allowed_hosts() -> list[str]:
    extra = _csv("SPIKECLIP_ALLOWED_HOSTS") + _csv("RENDER_EXTERNAL_HOSTNAME")
    return ["*"] if "*" in extra else LOCAL_HOSTS + extra


def is_public(path: str) -> bool:
    return path in PUBLIC_PATHS or "/callback" in path


def check_bind(host: str) -> None:
    """Refuse to serve an unauthenticated API on a public interface."""
    if host in ("127.0.0.1", "localhost", "::1"):
        return
    if api_token() or os.environ.get("SPIKECLIP_INSECURE_NO_AUTH") == "1":
        return
    raise SystemExit(
        f"Refusing to listen on {host} without {TOKEN_ENV}: this API reads and writes "
        f"files and has no other protection. Set {TOKEN_ENV} to a long random secret "
        "(or SPIKECLIP_INSECURE_NO_AUTH=1 for a container reachable only from this PC)."
    )


class TokenAuthMiddleware:
    """Pure ASGI, so it covers WebSockets as well as HTTP."""

    def __init__(self, app, token: str):
        self.app = app
        self.token = token.encode()

    def _presented(self, scope) -> bytes | None:
        for name, value in scope.get("headers") or []:
            if name == b"authorization" and value[:7].lower() == b"bearer ":
                return value[7:].strip()
            if name == TOKEN_HEADER:
                return value.strip()
        qs = parse_qs((scope.get("query_string") or b"").decode("latin-1"))
        got = qs.get(TOKEN_QUERY)
        return got[0].encode() if got else None

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            return await self.app(scope, receive, send)
        if scope["type"] == "http" and scope.get("method") == "OPTIONS":
            return await self.app(scope, receive, send)  # CORS preflight
        if is_public(scope.get("path", "")):
            return await self.app(scope, receive, send)
        presented = self._presented(scope)
        if presented is not None and hmac.compare_digest(presented, self.token):
            return await self.app(scope, receive, send)

        if scope["type"] == "websocket":
            await send({"type": "websocket.close", "code": 4401})
            return
        body = b'{"detail":"SpikeClip API token required"}'
        await send({
            "type": "http.response.start",
            "status": 401,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode()),
                (b"www-authenticate", b"Bearer"),
            ],
        })
        await send({"type": "http.response.body", "body": body})


def install_auth(app) -> bool:
    """Add token auth when a token is configured. Call before CORS is added,
    so CORS wraps it and a 401 still carries the CORS headers the browser
    needs to read it."""
    token = api_token()
    if token:
        app.add_middleware(TokenAuthMiddleware, token=token)
    return bool(token)
