# Kiselgram

Flask messaging platform (Python). WebRTC video calls via a separate SocketIO server.

## Essential commands

```bash
python3 manage.py start [--port PORT] [--no-video]   # start services
python3 manage.py stop                                 # graceful shutdown
python3 manage.py restart                              # stop + start
python3 manage.py setup                                # create dirs + default config
python3 manage.py reset-db                             # deletes ALL data
python3 manage.py status                               # check running ports
```

Config lives in `config/kis.toml` (not `.env`). The start command writes runner scripts to `/tmp/run_kiselgram.py` and forks background processes.

## Testing

```bash
.venv/bin/python -m pytest tests/ -v                        # all
.venv/bin/python -m pytest tests/test_models.py -v           # one file
.venv/bin/python -m pytest tests/test_models.py::TestUserModel::test_create_user -v  # one test
```

In-memory SQLite, tables truncated per test. Fixtures: `app` (session), `client`, `session` (function). Tests use `app.test_client()` and check JSON `success` field.

Test files are flat under `tests/` (one module per area: `test_auth.py`, `test_chats.py`, `test_models.py`, etc.). The `conftest.py` provides `user`, `user2`, `admin_user`, `premium_user` fixtures and session-based `logged_in_client` helpers.

## Architecture

**Two parallel route systems:**
- OLD (`app/routes/spa/`) — session-based, returns HTML redirects. Login route (`/auth/login` → redirects to `/app`) is still active; most other features migrated to V2.
- V2 (`app/routes/spav2/`) — JSON API, Bearer-token auth. All endpoints under `/api.v2/api/...`. Response shape: `{success: bool, data: {...}}` or `{success: false, error: {code, message}}`.

**Auth flow:** Bearer token (from `UserSession.session_token`) checked first; falls back to Flask `session['user_id']`. Helper: `get_current_user()` / `get_current_user_id()` in `app/utils/helpers.py`.

**Frontend SPA** — `templates/k.html` (single monolithic HTML shell). 17 JS modules in `static/js/k/` extending `window.K`. Load order matters:
```
init → api → ui → auth → views → chat → contacts → modals → groups
→ stories → saved → calls → music → webapp → search → settings → profile
```

JS globals: `$('id')` = `document.getElementById`, `esc()` for HTML escaping, `fmtTime()` for relative timestamps, `V2 = '/api.v2/api'`. No sockets, no SSR — pure `fetch()`-based.

**Security** (`app/utils/security.py`):
- CSP, security headers injected via `after_request` in `create_app()`
- Rate limiter is in-memory (not Redis), cleaned up on `teardown_appcontext`
- `X-Frame-Options` deliberately **not** set (webapp iframes need cross-origin framing)
- `frame-src` CSP allows `https:` and `http:` (for bot webapp iframes)
- Iframe sandbox uses `allow-scripts allow-forms allow-popups` (no `allow-same-origin`)

## Docker / Deployment

```bash
docker compose build --no-cache && docker compose up -d   # full rebuild
docker compose restart nginx                               # nginx upstream cache fix
deploy.sh                                                   # local → server rsync + docker compose
```

`deploy.sh` does rsync → docker compose on root@kiselgram.ru. nginx proxies `/room/`, `/socket.io/`, `/join` to video server (`video:5001`), `/mailadmin/` to mailadmin (`mailadmin:5002`), everything else to app (`app:5000`). SSL via Let's Encrypt (`ssl/` dir, certbot webroot in `certbot/www/`).

**Docker Compose services:**
- `db` — postgres:15-alpine (persistent `pgdata` volume)
- `app` — gunicorn `wsgi:app --workers 4` (port 5000)
- `video` — `python video_server/app.py` (port 5001)
- `mailadmin` — standalone Flask app (mailadmin/Dockerfile, port 5002, Docker socket + mail config volumes)
- `mailserver` — docker-mailserver (Postfix/Dovecot/OpenDKIM, ports 25/465/587/993)
- `nginx` — nginx:alpine (ports 80/443)

Production detection: `DATABASE_URL` env var activates PostgreSQL; otherwise SQLite (local dev).

## Domain Architecture

```
kiselgram.ru          ─ Main site (landing page)
web.kiselgram.ru      ─ SPA (/k route)
app.kiselgram.ru      ─ Redirect to web.kiselgram.ru
api.kiselgram.ru      ─ API backend
cdn.kiselgram.ru      ─ Uploaded files (served from volume)
status.kiselgram.ru   ─ Service status page
desktop.kiselgram.ru  ─ Desktop client downloads
docs.kiselgram.ru     ─ Documentation (GitHub Pages)
```

All subdomains route to the same VPS (except docs which is on GitHub Pages). nginx handles routing:
- `kiselgram.ru` — landing page at `/`, everything else → `web.kiselgram.ru`
- `web.kiselgram.ru` — proxies to Flask; root redirects to `/auth/login`
- `app.kiselgram.ru` — 301 redirect to `web.kiselgram.ru`
- `api.kiselgram.ru` — proxies to Flask (API at `/api.v2/api/...`)
- `cdn.kiselgram.ru` — serves `/uploads/` from Docker volume with long cache; proxies everything else to Flask
- `desktop.kiselgram.ru` — static files from `/var/www/desktop`
- `docs.kiselgram.ru` — CNAME to `kiselgram.github.io` (GitHub Pages)

Single SSL cert SANs: `kiselgram.ru, web.kiselgram.ru, www.kiselgram.ru, api.kiselgram.ru, desktop.kiselgram.ru, app.kiselgram.ru, cdn.kiselgram.ru`
Docs is on GitHub Pages (separate SSL via their CDN).

See `docs/domain.md` for full details.

## Mail Admin GUI

Standalone container at `mailadmin/` for managing mail accounts on the mail server. Accessible at `https://kiselgram.ru/mailadmin/` (login password set via `MAILADMIN_PASSWORD` env var in docker-compose.yml).

**API endpoints** (all require session auth):
- `GET /api/accounts` — list accounts
- `POST /api/accounts` — create (`{email, password}`)
- `DELETE /api/accounts/<email>` — delete
- `POST /api/accounts/<email>/password` — reset password (`{password}`)

After changes, the mail container is restarted in a background thread. The container has:
- Docker socket mounted (`:ro`) to exec into the mail container
- `mailserver/config` mounted (`:rw`) to read/write `postfix-accounts.cf`
- Nginx routes `/mailadmin/` → mailadmin:5002; a `PrefixMiddleware` in `app.py` sets `SCRIPT_NAME` from the `X-Forwarded-Prefix` header so redirects use the correct path.

Rebuild after code changes: `docker compose build mailadmin && docker compose up -d mailadmin`

## Key gotchas

- `manage.py start` kills whatever is on the target port first
- The V2 API prefix is `/api.v2/api` (parent `/api.v2` + child `/api`)
- V1 SPA login route (`app/routes/spa/auth.py`) redirects to `/app` on success; the flat `app/routes/auth.py` is dead code
- JS uses `K.chat._lastMsgId` cache to skip re-render when newest message hasn't changed
- 16MB upload limit for all file types (images, docs, video, audio)
- `.env` is local dev only (contains OPENROUTER_API_KEY); production secrets in `config/kis.toml`
- Video server `video_server/app.py` uses absolute `template_folder` path (derived from `__file__`) — Flask's `root_path` differs when run as `python video_server/app.py` vs via gunicorn
- Video server's `_ensure_db()` creates the main Flask app for DB access but does NOT push its context globally (uses `with _main_app.app_context():` in `_resolve_user()` instead)
- V3-only endpoints (QR login, email/login_v3) are registered under `/api.v2/` as well so the desktop client's single base URL works for all login flows
- `docker compose up -d --build` recreates app and video containers but does NOT restart nginx; run `docker compose restart nginx` if nginx returns 502 (stale upstream)

## Desktop Client (moved)

The JavaFX desktop app was moved to `~/PycharmProjects/kiselgram-desktop`. See its own `AGENTS.md` or README there for build/run instructions.

**Distribution zips** at `desktop-site/download/` in this repo:
- `Kiselgram-mac-arm64.zip` (38 MB, self-contained .app)
- `Kiselgram-mac-intel.zip` (1.5 MB, needs Java 21)
- `Kiselgram-windows.zip` (1.5 MB, needs Java 21)

API notes (server-side, applies to all clients including desktop):
- `AuthApi.pollQr()` -> server path: `/auth/qr/status/{token}`
- `ChatApi.sendTyping()` -> server path: `/typing/{chatType}/{chatId}` (chatType=`personal`, not `private`)
- QR login + email login endpoints are registered under both `/api.v2/` and `/api.v3/` (see `spav2/__init__.py`)
