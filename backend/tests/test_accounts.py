"""server/accounts.py: web sign-up, log-in and sessions behind the cloud token."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from server import accounts, cloud

ADMIN = "admin-token-for-tests"


def _client(monkeypatch, tmp_path, **env):
    monkeypatch.setenv("SPIKECLIP_API_TOKEN", ADMIN)
    for k in ("SPIKECLIP_INVITE_CODE", "SPIKECLIP_OPEN_SIGNUP"):
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    app = FastAPI()
    cloud.install_auth(app)
    acc = accounts.install(app, tmp_path)
    monkeypatch.setattr(cloud, "SESSION_CHECK", acc.session_valid)

    @app.get("/videos")
    def videos():
        return []

    return TestClient(app, base_url="http://127.0.0.1")


def test_sign_up_is_closed_without_an_invite_code(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path)
    assert client.get("/auth/config").json() == {"signup": "closed"}
    r = client.post("/auth/register", json={"email": "a@b.co", "password": "longenough"})
    assert r.status_code == 400 and "closed" in r.json()["detail"]


def test_an_invite_code_lets_people_in_and_their_session_opens_the_api(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path, SPIKECLIP_INVITE_CODE="vice-city")
    assert client.get("/auth/config").json() == {"signup": "invite"}
    bad = client.post("/auth/register", json={"email": "a@b.co", "password": "longenough", "invite": "nope"})
    assert bad.status_code == 400
    ok = client.post("/auth/register", json={"email": "a@b.co", "password": "longenough",
                                             "name": "Jason", "invite": "vice-city"})
    assert ok.status_code == 200
    token = ok.json()["token"]
    assert client.get("/videos").status_code == 401
    assert client.get("/videos", headers={"Authorization": f"Bearer {token}"}).status_code == 200
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json()["user"]
    assert me["email"] == "a@b.co" and me["name"] == "Jason"


def test_log_in_log_out_and_duplicates(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path, SPIKECLIP_OPEN_SIGNUP="1")
    client.post("/auth/register", json={"email": "Lucia@Vice.city", "password": "longenough"})
    again = client.post("/auth/register", json={"email": "lucia@vice.city", "password": "longenough"})
    assert again.status_code == 400
    assert client.post("/auth/login", json={"email": "lucia@vice.city", "password": "wrong-one"}).status_code == 401
    token = client.post("/auth/login", json={"email": "lucia@vice.city", "password": "longenough"}).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/videos", headers=headers).status_code == 200
    client.post("/auth/logout", headers=headers)
    assert client.get("/videos", headers=headers).status_code == 401


def test_weak_input_is_refused(monkeypatch, tmp_path):
    client = _client(monkeypatch, tmp_path, SPIKECLIP_OPEN_SIGNUP="1")
    assert client.post("/auth/register", json={"email": "nope", "password": "longenough"}).status_code == 400
    assert client.post("/auth/register", json={"email": "a@b.co", "password": "short"}).status_code == 400
