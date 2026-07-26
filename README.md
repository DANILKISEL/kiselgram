# Kiselgram

> Frontend: **Kiselgram K v4.7** · Backend: **Kiselgram PyFla v4.8**

Flask messaging platform — personal chats, groups, channels, stories, and WebRTC video calls. JSON API with a pure-JS single-page app frontend.

**⚠️ Kiselgram 5 coming — this Flask backend will be deprecated.**

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 manage.py setup     # create directories + default config
python3 manage.py start     # runs on http://localhost:5500
```

## Management

```bash
python3 manage.py start [--port PORT] [--no-video]
python3 manage.py stop
python3 manage.py restart
python3 manage.py status
python3 manage.py reset-db     # deletes ALL data
python3 manage.py routes       # list registered routes
python3 manage.py backup-db    # dump tables to JSON
python3 manage.py shell        # interactive Flask shell
```

Testing:

```bash
.venv/bin/python -m pytest tests/ -v
```

## Architecture

**Backend:** Python 3 / Flask / SQLAlchemy. Config in `config/kis.toml`. SQLite in dev, PostgreSQL in production (set `DATABASE_URL`).

**Two route systems:**
- V1 (`app/routes/spa/`) — session-based, returns HTML redirects. Legacy; login (`/auth/login` → `/k#login`) still active.
- V2 (`app/routes/spav2/`) — JSON API, Bearer-token auth. All endpoints under `/api.v2/api/...`. Response shape: `{success: bool, data: {...}}` or `{success: false, error: {code, message}}`.

**Auth:** Bearer token from `UserSession.session_token` checked first; falls back to Flask `session['user_id']`. Helper: `get_current_user()`.

**Message encryption:** All message content encrypted at rest using AES-256-GCM (Fernet). Transparent model property — encrypts on set, decrypts on get. Key via `MESSAGE_ENCRYPTION_KEY` env var. Graceful plaintext fallback when unset.

**Frontend:** Single monolithic HTML (`templates/k.html`) with 17+ JS modules in `static/js/k/` extending `window.K`. No sockets, no SSR — pure `fetch()`-based SPA.

**Security:** CSP headers, in-memory rate limiter, `@json_only` decorator, input sanitization, message payload encryption.

## Domain structure

```
kiselgram.ru              ─ Main site (landing page)
web.kiselgram.ru          ─ SPA (web app)
app.kiselgram.ru          ─ Redirects to web.kiselgram.ru
api.kiselgram.ru          ─ API backend
admin.kiselgram.ru        ─ Admin panel
cdn.kiselgram.ru          ─ Uploaded files
status.kiselgram.ru       ─ Service status
desktop.kiselgram.ru      ─ Desktop downloads
docs.kiselgram.ru         ─ Documentation (GitHub Pages)
help.kiselgram.ru         ─ Help center (GitHub Pages)
call.kiselgram.ru         ─ Video call rooms
premium.kiselgram.ru      ─ Premium info
bugs.kiselgram.ru         ─ Bug reports (GitHub Issues)
mycode.3d.store.kiselgram.ru ─ Code generator + SPA access
```

## Deployment

```bash
# Build + deploy all services
docker build --platform linux/amd64 -t kiselgram-app:latest .
docker save kiselgram-app:latest | ssh root@kiselgram.ru docker load
rsync -avz --delete --exclude-from=.rsync-exclude . root@kiselgram.ru:/root/kiselgram/
ssh root@kiselgram.ru 'cd /root/kiselgram && docker compose up -d'
ssh root@kiselgram.ru 'cd /root/kiselgram && docker compose restart nginx'

# Or use deploy.sh
./deploy.sh
```

Production services: `db` (Postgres 15), `app` (gunicorn, port 5000), `video` (WebRTC, port 5001), `mailserver` (docker-mailserver), `mailadmin` (account management GUI), `nginx` (ports 80/443).

## Backend overview

| Directory | Purpose |
|-----------|---------|
| `app/routes/spav2/` | V2 API blueprints (auth, chats, messages, groups, channels, stories, contacts, profile, search, settings, admin, oauth, qr login, email login) |
| `app/models.py` | SQLAlchemy models (User, Chat, Message, Story, etc. — ~35 tables) |
| `app/utils/` | Helpers, security (rate limiting, CSP, CSRF), crypto (AES-256-GCM) |
| `static/js/k/` | SPA JS modules (init, api, ui, auth, chat, contacts, stories, etc.) |
| `static/css/` | Desktop + mobile + animations CSS |
| `config/kis.toml` | App configuration (secret key, OAuth keys, mail, etc.) |
| `migrations/` | Alembic migrations for PostgreSQL schema changes |
| `tests/` | Pytest fixtures + tests per area |

## License

MIT
