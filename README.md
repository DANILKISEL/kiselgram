# Kiselgram

Flask messaging platform — personal chats, groups, channels, stories, and WebRTC video calls. JSON API with a pure-JS single-page app frontend.

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

**Frontend:** Single monolithic HTML (`templates/k.html`) with 17+ JS modules in `static/js/k/` extending `window.K`. No sockets, no SSR — pure `fetch()`-based SPA.

**Security:** CSP headers, in-memory rate limiter, `@json_only` decorator, input sanitization.

## Domain structure

```
kiselgram.ru          ─ Main site (landing page)
web.kiselgram.ru      ─ SPA (web app)
api.kiselgram.ru      ─ API backend
desktop.kiselgram.ru  ─ Desktop downloads (GitHub Pages)
docs.kiselgram.ru     ─ Documentation (GitHub Pages)
```

## Deployment

```bash
docker compose build --no-cache && docker compose up -d
docker compose restart nginx    # after app rebuild
```

Production services: `db` (Postgres), `app` (gunicorn, port 5000), `nginx` (ports 80/443), plus video and mail servers. SSL via Let's Encrypt. See `deploy.sh` for rsync + docker compose flow.

## Backend overview

| Directory | Purpose |
|-----------|---------|
| `app/routes/spav2/` | V2 API blueprints (auth, chats, messages, groups, channels, stories, contacts, profile, search, settings, admin, oauth, qr login, email login) |
| `app/models.py` | SQLAlchemy models (User, Chat, Message, Story, etc. — ~35 tables) |
| `app/utils/` | Helpers, security (rate limiting, CSP, CSRF) |
| `static/js/k/` | SPA JS modules (init, api, ui, auth, chat, contacts, stories, etc.) |
| `static/css/` | Desktop + mobile + animations CSS |
| `config/kis.toml` | App configuration (secret key, OAuth keys, mail, etc.) |
| `migrations/` | Alembic migrations for PostgreSQL schema changes |
| `tests/` | Pytest fixtures + tests per area |

## License

MIT
