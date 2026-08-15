from flask import Flask, render_template, request, jsonify, redirect, session, abort
import subprocess
import json
import os
import hmac
import hashlib

app = Flask(__name__)
app.secret_key = os.environ.get('MAILADMIN_SECRET', 'dev')

ADMINS = os.environ.get('MAILADMIN_ADMINS', 'postmaster@kiselgram.ru,postmaster@mail.kiselgram.ru').split(',')
DOMAINS = os.environ.get('MAILADMIN_DOMAINS', 'kiselgram.ru,mail.kiselgram.ru').split(',')
INTERNAL_KEY = os.environ.get('MAILADMIN_INTERNAL_KEY', '')

ACCOUNTS_FILE = '/mailconfig/postfix-accounts.cf'
VIRTUAL_FILE = '/mailconfig/postfix-virtual.cf'


def _docker():
    return subprocess.run(['docker', 'ps', '--filter', 'name=kiselgram-mailserver-1', '--format', '{{.ID}}'],
                          capture_output=True, text=True).stdout.strip()


def _read_accounts():
    accounts = {}
    try:
        with open(ACCOUNTS_FILE) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                email, hashed = line.split('|', 1)
                accounts[email] = hashed
    except FileNotFoundError:
        pass
    return accounts


def _write_accounts(accounts):
    with open(ACCOUNTS_FILE, 'w') as f:
        for email, hashed in sorted(accounts.items()):
            f.write(f'{email}|{hashed}\n')


def _restart_mail():
    container = _docker()
    if container:
        subprocess.run(['docker', 'restart', container], capture_output=True, text=True)


def _verify_password(email, password):
    hashed = _read_accounts().get(email)
    if not hashed:
        return False
    return _dovecot_verify(email, hashed, password)


def _dovecot_verify(email, hashed, password):
    import crypt
    import base64
    import hashlib
    algorithm, salt, _ = hashed.split('$')[1:4]
    if algorithm == '6':
        candidate = crypt.crypt(password, f'$6${salt}$')
    elif algorithm == '5':
        candidate = crypt.crypt(password, f'$5${salt}$')
    elif algorithm == '2y' or algorithm == '2a' or algorithm == '2b':
        import bcrypt
        candidate = bcrypt.hashpw(password.encode(), hashed.encode()).decode()
    else:
        return False
    return hmac.compare_digest(candidate, hashed)


def _hash_password(password):
    import crypt
    salt = os.urandom(12).hex()
    return crypt.crypt(password, f'$6${salt}$')


def _is_admin(email):
    return email in ADMINS


class PrefixMiddleware(object):
    def __init__(self, wsgi_app, prefix='/mailadmin'):
        self.wsgi_app = wsgi_app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        if path.startswith(self.prefix):
            environ['PATH_INFO'] = path[len(self.prefix):]
        return self.wsgi_app(environ, start_response)


app.wsgi_app = PrefixMiddleware(app.wsgi_app)


@app.route('/')
def index():
    return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').lower()
        password = request.form.get('password', '')
        if _verify_password(email, password) and _is_admin(email):
            session['admin'] = email
            return redirect('/mailadmin/accounts')
        return render_template('login.html', error='Неверный логин или пароль')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/mailadmin/')


def _admin_only():
    if not session.get('admin'):
        abort(401)


@app.route('/api/accounts')
@_admin_only
@login_required
@app.route('/api/accounts')
@_admin_only
@login_required
