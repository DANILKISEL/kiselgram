# 🚀 Kiselgram – Deploy & Restart

This guide assumes you already have a working Kiselgram installation on your server. All commands are run as **root** without `sudo`.

---

## 📤 Upload Files from Your Local Machine

From your **local Mac**, run:

```bash
rsync -avz -e "ssh -i ~/.ssh/id_ed25519" \
    --exclude 'venv/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude '.git/' \
    --exclude '.idea/' \
    --exclude '.DS_Store' \
    --exclude 'uploads/' \
    --exclude 'instance/' \
    --exclude 'logs/' \
    --exclude '.env' \
    --exclude '*.db' \
    /Users/dkisel/PycharmProjects/kiselgram-dev/ \
    root@kiselgram.ru:/var/www/kiselgram/
```
Replace:

/Users/dkisel/PycharmProjects/kiselgram-dev/ with your local project path

---

## 📦 Deploy Updated Code

### If you uploaded new files via `scp` or `rsync`:

```bash
cd /var/www/kiselgram
source venv/bin/activate
pip install -r requirements.txt --quiet
```

### If you need to update the database schema:

```bash
cd /var/www/kiselgram
source venv/bin/activate
python3 -c "
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print('✅ Database updated')
"
```

---

## 🔄 Restart Services

```bash
supervisorctl restart kiselgram_group:kiselgram
systemctl reload nginx
```

---

## ✅ Verify Deployment

```bash
# Check Gunicorn is running
supervisorctl status

# Test locally
# RUN ONLY ON SERVER
curl -I http://127.0.0.1:8000/

# Test through Nginx
curl -I http://web.kiselgram.ru/

# Check Nginx status
systemctl status nginx --no-pager | head -5
```

Visit `http://YOUR_SERVER_IP` in a browser to confirm the site is live.

---

## 📝 Quick Reference

| Task | Command |
|------|---------|
| Restart app | `supervisorctl restart kiselgram_group:kiselgram` |
| View Gunicorn logs | `tail -f /var/www/kiselgram/logs/gunicorn_error.log` |
| View Nginx logs | `tail -f /var/log/nginx/kiselgram_error.log` |
| Check Gunicorn status | `supervisorctl status` |
