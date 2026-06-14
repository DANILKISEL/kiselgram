import os
import re
import crypt
import string
import random
import threading
import docker
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get('MAILADMIN_SECRET')
if not app.secret_key:
    raise RuntimeError("MAILADMIN_SECRET environment variable must be set")
app.config['SESSION_COOKIE_PATH'] = '/mailadmin/'

MAIL_CONTAINER = 'kiselgram-mailserver-1'
ACCOUNTS_FILE = '/mailconfig/postfix-accounts.cf'
ADMIN_EMAILS = [e.strip() for e in
                os.environ.get('MAILADMIN_ADMINS',
                               'postmaster@kiselgram.ru,postmaster@mail.kiselgram.ru')
                .split(',') if e.strip()]
DOMAINS = [d.strip() for d in
           os.environ.get('MAILADMIN_DOMAINS',
                          'kiselgram.ru,mail.kiselgram.ru')
           .split(',') if d.strip()]
INTERNAL_KEY = os.environ.get('MAILADMIN_INTERNAL_KEY')

def _docker():
    return docker.from_env()

def _read_accounts():
    if not os.path.exists(ACCOUNTS_FILE):
        return []
    accounts = []
    with open(ACCOUNTS_FILE) as f:
        for line in f:
            line = line.strip()
            if line and '|' in line:
                email, pwhash = line.split('|', 1)
                accounts.append({'email': email, 'hash': pwhash})
    return accounts

def _write_accounts(accounts):
    os.makedirs(os.path.dirname(ACCOUNTS_FILE), exist_ok=True)
    with open(ACCOUNTS_FILE, 'w') as f:
        for acc in accounts:
            f.write(f"{acc['email']}|{acc['hash']}\n")

def _restart_mail():
    try:
        _docker().containers.get(MAIL_CONTAINER).restart(timeout=30)
    except Exception as e:
        app.logger.error(f"Restart failed: {e}")

def _verify_password(email, password):
    accounts = _read_accounts()
    for acc in accounts:
        if acc['email'] == email:
            h = acc['hash']
            if h.startswith('{SHA512-CRYPT}'):
                h = h[len('{SHA512-CRYPT}'):]
            try:
                return crypt.crypt(password, h) == h
            except Exception:
                return False
    return False

def _hash_password(password):
    salt = ''.join(random.choices(string.ascii_letters + string.digits + './', k=16))
    return '{SHA512-CRYPT}' + crypt.crypt(password, f'$6${salt}')

def _is_admin(email):
    return email in ADMIN_EMAILS

class PrefixMiddleware:
    def __init__(self, wsgi_app, prefix='/mailadmin'):
        self.wsgi_app = wsgi_app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        if environ.get('HTTP_X_FORWARDED_PREFIX') == self.prefix:
            environ['SCRIPT_NAME'] = self.prefix
            path = environ.get('PATH_INFO', '')
            if path.startswith(self.prefix):
                environ['PATH_INFO'] = path[len(self.prefix):]
        return self.wsgi_app(environ, start_response)

app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix='/mailadmin')

# ── Pages ─────────────────────────────────────────────────────────

@app.route('/')
def index():
    if not session.get('authenticated') or 'email' not in session:
        session.clear()
        return redirect(url_for('login'))
    return render_template('accounts.html',
                           email=session['email'],
                           is_admin=session.get('is_admin', False),
                           domains=DOMAINS)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        if _verify_password(email, password):
            session['authenticated'] = True
            session['email'] = email
            session['is_admin'] = _is_admin(email)
            return redirect(url_for('index'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ── Admin Account API ──────────────────────────────────────────────

def _admin_only():
    if INTERNAL_KEY and request.headers.get('X-Internal-Key') == INTERNAL_KEY:
        return None
    if not session.get('authenticated'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    if not session.get('is_admin'):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

@app.route('/api/accounts')
def list_accounts():
    r = _admin_only()
    if r: return r
    return jsonify({'success': True, 'accounts': _read_accounts()})

@app.route('/api/accounts', methods=['POST'])
def add_account():
    r = _admin_only()
    if r: return r
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    if not email or not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return jsonify({'success': False, 'error': 'Invalid email'})
    if len(password) < 6:
        return jsonify({'success': False, 'error': 'Password must be 6+ characters'})
    accounts = _read_accounts()
    if any(a['email'] == email for a in accounts):
        return jsonify({'success': False, 'error': 'Account already exists'})
    try:
        container = _docker().containers.get(MAIL_CONTAINER)
        exit_code, output = container.exec_run(
            ['setup', 'email', 'add', email, password])
        if exit_code != 0:
            return jsonify({'success': False, 'error': output.decode().strip()})
        threading.Thread(target=_restart_mail, daemon=True).start()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/accounts/<path:email>', methods=['DELETE'])
def delete_account(email):
    r = _admin_only()
    if r: return r
    accounts = _read_accounts()
    accounts = [a for a in accounts if a['email'] != email]
    _write_accounts(accounts)
    threading.Thread(target=_restart_mail, daemon=True).start()
    return jsonify({'success': True})

@app.route('/api/accounts/<path:email>/password', methods=['POST'])
def reset_password(email):
    r = _admin_only()
    if r: return r
    data = request.get_json() or {}
    password = data.get('password', '')
    if len(password) < 6:
        return jsonify({'success': False, 'error': 'Password must be 6+ characters'})
    try:
        container = _docker().containers.get(MAIL_CONTAINER)
        exit_code, output = container.exec_run(
            ['setup', 'email', 'update', email, password])
        if exit_code != 0:
            out = output.decode()
            if 'does not exist' in out:
                accounts = _read_accounts()
                accounts = [a for a in accounts if a['email'] != email]
                _write_accounts(accounts)
            return jsonify({'success': False, 'error': out.strip()})
        threading.Thread(target=_restart_mail, daemon=True).start()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ── User self-service API ──────────────────────────────────────────

@app.route('/api/me')
def get_my_account():
    if not session.get('authenticated'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    email = session['email']
    accounts = _read_accounts()
    for acc in accounts:
        if acc['email'] == email:
            return jsonify({'success': True, 'account': acc})
    return jsonify({'success': False, 'error': 'Not found'}), 404

@app.route('/api/me/password', methods=['POST'])
def change_my_password():
    if not session.get('authenticated'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    email = session['email']
    data = request.get_json() or {}
    cur = data.get('current_password', '')
    new = data.get('new_password', '')
    if not cur or not new:
        return jsonify({'success': False, 'error': 'Missing fields'})
    if len(new) < 6:
        return jsonify({'success': False, 'error': 'Minimum 6 characters'})
    if not _verify_password(email, cur):
        return jsonify({'success': False, 'error': 'Current password is wrong'})
    accounts = _read_accounts()
    for acc in accounts:
        if acc['email'] == email:
            acc['hash'] = _hash_password(new)
            break
    _write_accounts(accounts)
    return jsonify({'success': True})

@app.route('/api/me/email', methods=['POST'])
def change_my_email():
    if not session.get('authenticated'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    email = session['email']
    data = request.get_json() or {}
    new_email = data.get('new_email', '').strip().lower()
    password = data.get('password', '')
    if not new_email or not re.match(r'^[^@]+@[^@]+\.[^@]+$', new_email):
        return jsonify({'success': False, 'error': 'Invalid email'})
    if not password:
        return jsonify({'success': False, 'error': 'Password required'})
    if not _verify_password(email, password):
        return jsonify({'success': False, 'error': 'Password is wrong'})
    accounts = _read_accounts()
    if any(a['email'] == new_email for a in accounts):
        return jsonify({'success': False, 'error': 'Email already exists'})
    try:
        container = _docker().containers.get(MAIL_CONTAINER)
        exit_code, output = container.exec_run(
            ['setup', 'email', 'add', new_email, password])
        if exit_code != 0:
            return jsonify({'success': False, 'error': output.decode().strip()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    accounts = [a for a in accounts if a['email'] != email]
    _write_accounts(accounts)
    session['email'] = new_email
    threading.Thread(target=_restart_mail, daemon=True).start()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
