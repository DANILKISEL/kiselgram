# Domain Architecture

```
kiselgram.ru          ─ Main site (landing page)
web.kiselgram.ru      ─ SPA (single-page app)
api.kiselgram.ru      ─ API backend (Flask)
desktop.kiselgram.ru  ─ Desktop client downloads (VPS nginx → GitHub Pages TBD)
docs.kiselgram.ru     ─ Documentation (VPS nginx → GitHub Pages TBD)
```

## Service → Subdomain mapping

| Subdomain           | Target               | Hosting                |
|---------------------|----------------------|------------------------|
| `kiselgram.ru`      | Landing page         | VPS (nginx → Flask)    |
| `web.kiselgram.ru`  | SPA (`/k`)           | VPS (nginx → Flask)    |
| `api.kiselgram.ru`  | API backend          | VPS (nginx → Flask)    |
| `desktop.kiselgram.ru` | Desktop zips     | VPS nginx (static)     |
| `docs.kiselgram.ru` | Documentation        | VPS nginx (static)     |

## GitHub Pages (future)

- `kiselgram/docs` → `docs.kiselgram.ru` (CNAME record to GitHub Pages IPs)
- `kiselgram/desktop-site` → `desktop.kiselgram.ru`

## nginx rules

- `kiselgram.ru` — landing page at `/`, everything else 301 → `web.kiselgram.ru`
- `web.kiselgram.ru` — proxy_pass to `app:5000`, root redirects to `/auth/login`
- `api.kiselgram.ru` — proxy_pass to `app:5000` (API routes)
- `desktop.kiselgram.ru` — static files from `/var/www/desktop`
- `docs.kiselgram.ru` — static files from `/var/www/docs`

## SSL

Single cert covering all domains, renewed nightly via certbot cron. Serves from `/root/kiselgram/ssl/fullchain.pem`.
