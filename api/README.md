# SpikeClip web API

A small service for the website and the desktop app: **accounts, Paddle payments and licence keys**.
It never touches video — finding chat spikes and cutting 9:16 clips happens in the desktop app on the
user's own PC (`frontend/` Electron shell + `backend/` engine, packaged together).

```
cd api
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8080     # http://localhost:8080/docs
pytest
```

Deploy: Docker (`api/Dockerfile`), e.g. Render with **Root Directory = `api`**. Environment: see
[`.env.example`](.env.example). Use Postgres (`DATABASE_URL`) in production — a free host without a
persistent disk deletes the SQLite file on every redeploy, and with it every customer's key.

## Data

| Table | What |
|---|---|
| `users` | website accounts (email lower-case, PBKDF2 password hash) |
| `sessions` | login sessions (SHA-256 of the token only) |
| `licenses` | `license_key` `CLIP-XXXX-XXXX-XXXX`, `plan` (pro/max), `status` (active, past_due, paused, canceled, revoked), `max_activations`, `expires_at`, `source` (paddle/manual), `paddle_subscription_id`, Paddle cancel / update-payment links |
| `activations` | one per (licence, device): SHA-256 of the app's device id, name, platform, app version, first/last seen |
| `paddle_events` | processed webhook event ids, so a retried event is applied once |

Schema: [`app/db.py`](app/db.py). Plans and what they unlock: [`app/settings.py`](app/settings.py) (`PLANS`).

## Endpoints

| Method & path | Who | What |
|---|---|---|
| `GET /health` | anyone | liveness |
| `GET /auth/config` · `POST /auth/register` · `POST /auth/login` · `POST /auth/logout` · `GET /auth/me` · `GET /auth/check` | website | accounts (`Authorization: Bearer sc_…` after login) |
| `GET /billing/config` | website | Paddle client token, price ids, environment |
| `POST /billing/paddle/webhook` | Paddle | signed `subscription.*` events → create / update the user's key |
| `GET /billing/me` | website | the user's best active plan + Paddle manage links |
| `GET /licenses/me` | website | the user's keys, devices and features |
| `DELETE /licenses/{key}/devices/{device}` | website | release a device from the account page |
| `POST /v1/license/activate` | desktop app | bind this device to the key |
| `POST /v1/license/validate` | desktop app | is the key still good on this device? |
| `POST /v1/license/deactivate` | desktop app | free this device's slot |
| `GET /v1/plans` | desktop app | limits per plan (incl. the keyless free trial) |
| `GET /downloads` | website | Windows / Mac build links and version |
| `POST /admin/licenses` · `GET /admin/licenses` · `POST /admin/licenses/{key}/revoke` | owner (`Bearer ADMIN_TOKEN`) | issue keys by hand (gifts, testers, reviewers), list, revoke |

### Desktop app contract

Request (all three `/v1/license/*` calls):

```json
{ "key": "CLIP-7K3M-Q9XW-2HPD", "device_id": "stable-random-id-of-this-install",
  "device_name": "Gaming PC", "platform": "windows", "app_version": "2.1.0" }
```

`device_id`: generate once per install (e.g. a UUID saved in the app's data folder); the server only
keeps its SHA-256.

Response:

```json
{ "ok": true, "code": "ok", "message": "License is active.",
  "check_again_after_hours": 72, "offline_grace_days": 7, "server_time": "2026-11-20T10:00:00Z",
  "license": { "key": "CLIP-…", "plan": "pro", "plan_label": "Pro", "status": "active", "state": "ok",
               "expires_at": "2026-12-20T10:00:00Z", "max_activations": 2, "activations_used": 1,
               "devices": [ … ], "features": { "clips_per_month": null, "watermark": false, "max_resolution": 1080 } } }
```

`code` is one of `ok`, `invalid_key`, `revoked`, `expired`, `inactive`, `activation_limit`,
`not_activated`; `message` is ready to show the user. Suggested app behaviour: activate on first
entry of the key; validate on start-up when `check_again_after_hours` has passed; if the server can't
be reached, keep working for `offline_grace_days` after the last good answer; without a key, run the
`free` plan from `/v1/plans`. Key endpoints are rate-limited per IP (`LICENSE_RATE_PER_MINUTE`, 30).
