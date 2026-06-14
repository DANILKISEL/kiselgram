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
admin.kiselgram.ru    ─ Admin panel (proxies to Flask, / → redirect to /api/admin/)
help.kiselgram.ru     ─ Redirects to kiselgram.github.io/help (GitHub Pages, repo github.com/kiselgram/help)
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

Single SSL cert SANs: `kiselgram.ru, web.kiselgram.ru, www.kiselgram.ru, api.kiselgram.ru, desktop.kiselgram.ru, app.kiselgram.ru, cdn.kiselgram.ru, admin.kiselgram.ru, help.kiselgram.ru`
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
- After server reboot, host nginx may grab port 80 before Docker nginx starts; run `systemctl stop nginx && systemctl disable nginx` on the host, then `docker compose up -d nginx`
- If nginx gets `host not found in upstream "app:5000"`, the container may not be on compose network. Fix: `docker compose create nginx && docker network connect kiselgram_default kiselgram-nginx-1 && docker start kiselgram-nginx-1`
- Building on Apple Silicon requires `--platform linux/amd64` for server (amd64 host). Transfer: `docker save <image> | ssh root@kiselgram.ru docker load` (avoid intermediate files — SCP/rsync gzip truncates large images).

## Desktop Client (moved)

The JavaFX desktop app was moved to `~/PycharmProjects/kiselgram-desktop`. See its own `AGENTS.md` or README there for build/run instructions.

**Distribution zips** at `desktop-site/download/` in this repo:
- `Kiselgram-mac-arm64.zip` (38 MB, self-contained .app)
- `Kiselgram-mac-intel.zip` (1.5 MB, needs Java 21)
- `Kiselgram-windows.zip` (1.5 MB, needs Java 21)
- `Kiselgram-K.app.zip` (2 KB, macOS Chrome launcher for the K version)

**PWA:** The K version (`/k` route) has a dedicated manifest (`static/manifest_k.json`) and registers the service worker (`static/js/sw.js`). Install via Chrome/Edge address bar "Install" button — opens as a standalone window. Pass `?view=desktop` to change title to "Kiselgram Desktop".

**Python webview wrapper** (`desktop_app.py` in repo root, also copied to `~/PycharmProjects/kiselgram-desktop/`):
```bash
pip3 install pywebview
python3 desktop_app.py                              # production (web.kiselgram.ru)
python3 desktop_app.py http://localhost:5000/k?view=desktop  # local dev
```

API notes (server-side, applies to all clients including desktop):
- `AuthApi.pollQr()` -> server path: `/auth/qr/status/{token}`
- `ChatApi.sendTyping()` -> server path: `/typing/{chatType}/{chatId}` (chatType=`personal`, not `private`)
- QR login + email login endpoints are registered under both `/api.v2/` and `/api.v3/` (see `spav2/__init__.py`)

## Session Summary (2026-06-11)

### Completed
- **Security audit fixes deployed**: Docker images rebuilt locally for `linux/amd64` and deployed to production. Includes:
  - Non-root `appuser` in both Dockerfiles + HEALTHCHECKs
  - Hardcoded secrets moved from docker-compose.yml to `.env` file (`.env.example` created)
  - JS fixes: try/catch wrappers for `JSON.parse(localStorage)`, error toasts instead of empty catches, CSS injection prevention in settings
  - `d.success` checks fixed, `parseInt` radix added
  - Video server `debug=False`, `allow_unsafe_werkzeug=False`
  - Profile upload extension whitelist
  - `/health` endpoint, expanded `.dockerignore`
- **Docker build moved off server**: Building on the 957MB RAM server caused OOM. Changed `docker-compose.yml` to use `image:` tags (no `build:`). Images are built locally on Mac (Apple Silicon with `--platform linux/amd64`) and transferred via `docker save | ssh docker load`.
- **deploy.sh updated**: Replaced server-side `docker compose build` with local build + `docker save | ssh docker load` pipeline.
- **Mail server pinned**: `docker-mailserver` image pinned to `14.0` (was `latest`). Nginx pinned to `1.27-alpine` (was `alpine`).
- **nginx replaced**: Host nginx was binding port 80 after reboot, preventing Docker nginx from starting. Disabled host nginx (`systemctl disable nginx`); Docker nginx now serves all traffic.

### Ongoing Issues
- **Server underpowered**: 957MB RAM / 512MB swap (old swapfile). Needs `fallocate -l 2G /swapfile` to prevent OOM during heavy operations.
- **Mailadmin container shows "unhealthy"**: No HEALTHCHECK defined in mailadmin Dockerfile — Docker defaults to unhealthy. Container works fine.
- **`.env` on server**: Created at `/root/kiselgram/.env` with `POSTGRES_PASSWORD`, `DATABASE_URL`, `MAILADMIN_INTERNAL_KEY`, `MAILADMIN_SECRET`.

### Key Decisions
- **No Docker builds on server** — build locally, pipe image via `docker save | ssh docker load`
- **`docker-compose.yml` uses `image:`** instead of `build:` for all custom services
- **Git-untracked files**: `.env` (all env vars), `config/kis.toml` (OAuth secrets, app config), `mailserver/config/` (mail accounts), `ssl/` (certificates)

### Deploy Workflow
```bash
# 1. Build locally
docker build --platform linux/amd64 -t kiselgram-app:latest .
docker build --platform linux/amd64 -t kiselgram-mailadmin:latest mailadmin/

# 2. Transfer + load on server
docker save kiselgram-app:latest | ssh root@kiselgram.ru docker load
docker save kiselgram-mailadmin:latest | ssh root@kiselgram.ru docker load

# 3. Rsync code + restart
rsync -avz --delete --exclude-from=.rsync-exclude . root@kiselgram.ru:/root/kiselgram/
ssh root@kiselgram.ru 'cd /root/kiselgram && docker compose up -d && docker compose restart nginx'
```
Or just run `./deploy.sh`.

### Server Architecture
- amd64 VM (hetzner?), 957MB RAM, 15GB disk
- Docker compose with 6 containers: db (postgres), app (Flask+gunicorn), video (Flask+eventlet), nginx (proxy), mailserver (docker-mailserver), mailadmin (Flask+gunicorn)
- nginx is Docker-based; host nginx was disabled (`systemctl disable nginx`)
- SSL cert with 12 SANs, Let's Encrypt via certbot in Docker
