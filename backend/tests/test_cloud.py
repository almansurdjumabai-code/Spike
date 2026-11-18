"""server/cloud.py: the cloud deployment's token, CORS and host settings."""

import pytest
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.websockets import WebSocketDisconnect

from server import cloud

try:  # newer Starlette reports a close before accept as an HTTP denial
    from starlette.testclient import WebSocketDenialResponse
    REFUSED = (WebSocketDisconnect, WebSocketDenialResponse)
except ImportError:
    REFUSED = (WebSocketDisconnect,)

TOKEN = "s3cret-token-for-tests"
FRONTEND = "https://app.spikeclip.test"


def _app(monkeypatch, token=TOKEN):
    if token:
        monkeypatch.setenv("SPIKECLIP_API_TOKEN", token)
    else:
        monkeypatch.delenv("SPIKECLIP_API_TOKEN", raising=False)
    monkeypatch.setenv("SPIKECLIP_CORS_ORIGINS", FRONTEND + "/")
    monkeypatch.setenv("SPIKECLIP_ALLOWED_HOSTS", "api.spikeclip.test")
    app = FastAPI()
    cloud.install_auth(app)
    app.add_middleware(CORSMiddleware, allow_origins=cloud.cors_origins(),
                       allow_methods=["*"], allow_headers=["*"])
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=cloud.allowed_hosts())

    @app.get("/health")
    def health():
        return {"ok": True}

    @app.get("/videos")
    def videos():
        return []

    @app.get("/discord/callback")
    def callback():
        return {"ok": True}

    @app.websocket("/ws")
    async def ws(socket: WebSocket):
        await socket.accept()
        await socket.send_json({"hello": 1})
        await socket.close()

    return TestClient(app, base_url="https://api.spikeclip.test")


def test_without_a_token_nothing_changes(monkeypatch):
    client = _app(monkeypatch, token=None)
    assert client.get("/videos").status_code == 200


def test_every_route_but_health_and_callbacks_needs_the_token(monkeypatch):
    client = _app(monkeypatch)
    assert client.get("/health").status_code == 200
    assert client.get("/discord/callback").status_code == 200
    assert client.get("/videos").status_code == 401
    assert client.get("/videos", headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert client.get("/videos", headers={"Authorization": f"Bearer {TOKEN}"}).status_code == 200
    assert client.get("/videos", headers={"X-SpikeClip-Token": TOKEN}).status_code == 200
    assert client.get(f"/videos?access_token={TOKEN}").status_code == 200


def test_a_401_still_carries_cors_headers_and_preflight_passes(monkeypatch):
    client = _app(monkeypatch)
    denied = client.get("/videos", headers={"Origin": FRONTEND})
    assert denied.status_code == 401
    assert denied.headers["access-control-allow-origin"] == FRONTEND
    pre = client.options("/videos", headers={"Origin": FRONTEND, "Access-Control-Request-Method": "GET",
                                              "Access-Control-Request-Headers": "authorization"})
    assert pre.status_code == 200


def test_the_websocket_needs_the_token_in_its_url(monkeypatch):
    client = _app(monkeypatch)
    with pytest.raises(REFUSED):
        with client.websocket_connect("wss://api.spikeclip.test/ws") as socket:
            socket.receive_json()
    with client.websocket_connect(f"wss://api.spikeclip.test/ws?access_token={TOKEN}") as socket:
        assert socket.receive_json() == {"hello": 1}


def test_unknown_hosts_are_refused(monkeypatch):
    client = _app(monkeypatch)
    assert client.get("/health", headers={"Host": "evil.test"}).status_code == 400


def test_render_s_own_host_name_is_allowed(monkeypatch):
    monkeypatch.delenv("SPIKECLIP_ALLOWED_HOSTS", raising=False)
    monkeypatch.setenv("RENDER_EXTERNAL_HOSTNAME", "spikeclip-backend.onrender.com")
    assert "spikeclip-backend.onrender.com" in cloud.allowed_hosts()


def test_a_public_bind_needs_a_token(monkeypatch):
    monkeypatch.delenv("SPIKECLIP_API_TOKEN", raising=False)
    monkeypatch.delenv("SPIKECLIP_INSECURE_NO_AUTH", raising=False)
    cloud.check_bind("127.0.0.1")
    with pytest.raises(SystemExit):
        cloud.check_bind("0.0.0.0")
    monkeypatch.setenv("SPIKECLIP_API_TOKEN", TOKEN)
    cloud.check_bind("0.0.0.0")
    monkeypatch.delenv("SPIKECLIP_API_TOKEN")
    monkeypatch.setenv("SPIKECLIP_INSECURE_NO_AUTH", "1")
    cloud.check_bind("0.0.0.0")
