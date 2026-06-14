import time
import re
import hashlib
import hmac
import secrets
from functools import wraps
from flask import request, jsonify, session, current_app, g

# ─── CSP ───────────────────────────────────────────────────────────────────

CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://kit.fontawesome.com https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://kit.fontawesome.com https://cdn.jsdelivr.net https://fonts.googleapis.com https://cdnjs.cloudflare.com https://p.typekit.net https://use.typekit.net; "
    "font-src 'self' data: https://kit.fontawesome.com https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
    "img-src 'self' data: blob:; "
    "media-src 'self' blob:; "
    "connect-src 'self' ws: wss:; "
    "frame-src 'self' https: http:; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)

SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-XSS-Protection': '0',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'geolocation=()',
}

def add_security_headers(resp):
    for k, v in SECURITY_HEADERS.items():
        resp.headers.setdefault(k, v)
    resp.headers.setdefault('Content-Security-Policy', CSP_POLICY)
    if request.is_secure:
        resp.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
    path = getattr(request, 'path', '') or ''
    if path.startswith('/api') or path.startswith('/api.v2') or path.startswith('/api.v3'):
        resp.headers.setdefault('Cache-Control', 'no-store')
    else:
        resp.headers.setdefault('Cache-Control', 'no-cache')
    return resp

# ─── RATE LIMITER ──────────────────────────────────────────────────────────

class RateLimiter:
    def __init__(self):
        self._store = {}

    def _key(self, ip, route):
        return f"{ip}:{route}"

    def check(self, route, max_requests=10, window=60):
        ip = request.remote_addr or 'unknown'
        key = self._key(ip, route)
        now = time.time()
        entry = self._store.get(key)
        if entry is None:
            self._store[key] = {'count': 1, 'reset': now + window}
            return True
        if now > entry['reset']:
            self._store[key] = {'count': 1, 'reset': now + window}
            return True
        entry['count'] += 1
        if entry['count'] > max_requests:
            return False
        return True

    def cleanup(self, max_age=300):
        now = time.time()
        stale = [k for k, v in self._store.items() if now > v['reset'] + max_age]
        for k in stale:
            del self._store[k]

rate_limiter = RateLimiter()

def rate_limit(route, max_requests=10, window=60):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not rate_limiter.check(route, max_requests, window):
                return jsonify({
                    'success': False,
                    'error': {'code': 'RATE_LIMITED', 'message': 'Too many requests. Please slow down.'}
                }), 429
            return f(*args, **kwargs)
        return wrapper
    return decorator

# ─── CSRF ───────────────────────────────────────────────────────────────────

def generate_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']

def validate_csrf_token(token):
    stored = session.get('csrf_token')
    if not stored or not token:
        return False
    return hmac.compare_digest(stored, token)

def require_csrf(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            # Skip CSRF check for Bearer-token-authenticated requests
            auth = request.headers.get('Authorization', '')
            if auth.startswith('Bearer '):
                return f(*args, **kwargs)
            token = request.headers.get('X-CSRF-Token', '') or request.form.get('csrf_token', '')
            if not validate_csrf_token(token):
                return jsonify({
                    'success': False,
                    'error': {'code': 'CSRF_FAILED', 'message': 'CSRF token missing or invalid'}
                }), 403
        return f(*args, **kwargs)
    return wrapper

# ─── PASSWORD POLICY ────────────────────────────────────────────────────────

def validate_password(password):
    errors = []
    if len(password) < 8:
        errors.append('Password must be at least 8 characters')
    if len(password) > 128:
        errors.append('Password must be at most 128 characters')
    if not re.search(r'[A-Za-z]', password):
        errors.append('Password must contain at least one letter')
    if not re.search(r'[0-9]', password):
        errors.append('Password must contain at least one digit')
    return errors

# ─── INPUT SANITIZATION ─────────────────────────────────────────────────────

def sanitize_string(value, max_length=200):
    if not isinstance(value, str):
        return ''
    value = value.strip()
    if len(value) > max_length:
        value = value[:max_length]
    # Strip control characters except newline and tab
    value = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', value)
    return value

def sanitize_html(value):
    if not isinstance(value, str):
        return ''
    # Strip script tags and event handlers
    value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.DOTALL | re.IGNORECASE)
    value = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', value, flags=re.IGNORECASE)
    value = re.sub(r'on\w+\s*=\s*\S+', '', value, flags=re.IGNORECASE)
    value = re.sub(r'javascript\s*:', '', value, flags=re.IGNORECASE)
    return value
