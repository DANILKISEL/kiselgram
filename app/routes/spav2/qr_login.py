from flask import Blueprint, request, jsonify, session, current_app
from datetime import datetime, timezone, timedelta
import secrets
from app import db
from app.models import User, UserSession, QrLoginToken
from app.utils.helpers import get_current_user
from app.utils.security import rate_limit

spav2_qr_bp = Blueprint('spav2_qr', __name__, url_prefix='/api/auth/qr')

# ── Mode A: "Get scanned" ──────────────────────────────────────
# Logged-in device generates a QR; scanner logs in as this user.

@spav2_qr_bp.route('/generate', methods=['POST'])
@rate_limit('qr_generate', max_requests=10, window=60)
def qr_generate():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=2)
    qr = QrLoginToken(user_id=user.id, token=token, expires_at=expires_at)
    db.session.add(qr)
    db.session.commit()

    return jsonify({'success': True, 'data': {
        'token': token,
        'expires_at': expires_at.isoformat(),
        'expires_in': 120,
    }})


# ── Mode B: "Scan QR" ──────────────────────────────────────────
# Unauthenticated device requests a QR; a logged-in device scans
# and authorizes it; the requesting device then logs in.

@spav2_qr_bp.route('/request', methods=['POST'])
@rate_limit('qr_request', max_requests=10, window=60)
def qr_request():
    """Public: create an unclaimed token for Mode B."""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=2)
    qr = QrLoginToken(user_id=None, token=token, expires_at=expires_at)
    db.session.add(qr)
    db.session.commit()

    return jsonify({'success': True, 'data': {
        'token': token,
        'expires_at': expires_at.isoformat(),
        'expires_in': 120,
    }})


@spav2_qr_bp.route('/authorize', methods=['POST'])
@rate_limit('qr_authorize', max_requests=10, window=60)
def qr_authorize():
    """Auth required: scan a Mode B QR and authorize the requesting device."""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    data = request.get_json() or {}
    token = data.get('token', '').strip()
    if not token:
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Token required'}}), 400

    qr = QrLoginToken.query.filter_by(token=token, consumed=False).first()
    if not qr:
        return jsonify({'success': False, 'error': {'code': 'INVALID_TOKEN', 'message': 'Invalid or expired QR code'}}), 400
    if qr.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        qr.consumed = True
        qr.consumed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.session.commit()
        return jsonify({'success': False, 'error': {'code': 'EXPIRED_TOKEN', 'message': 'QR code has expired'}}), 400
    if qr.user_id is not None:
        return jsonify({'success': False, 'error': {'code': 'ALREADY_LINKED', 'message': 'This QR is already linked to a user'}}), 400

    qr.user_id = user.id
    qr.authorized_by_id = user.id
    db.session.commit()

    return jsonify({'success': True, 'data': {'message': 'Login authorized'}})


# ── Shared: complete the login ─────────────────────────────────

@spav2_qr_bp.route('/login', methods=['POST'])
@rate_limit('qr_login', max_requests=5, window=60)
def qr_login():
    """Public: finalize login after the token has a linked user."""
    data = request.get_json() or {}
    token = data.get('token', '').strip()
    if not token:
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Token required'}}), 400

    qr = QrLoginToken.query.filter_by(token=token, consumed=False).first()
    if not qr:
        return jsonify({'success': False, 'error': {'code': 'INVALID_TOKEN', 'message': 'Invalid or expired QR code'}}), 400
    if qr.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        qr.consumed = True
        qr.consumed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.session.commit()
        return jsonify({'success': False, 'error': {'code': 'EXPIRED_TOKEN', 'message': 'QR code has expired'}}), 400
    if qr.user_id is None:
        return jsonify({'success': False, 'error': {'code': 'NOT_AUTHORIZED', 'message': 'Not yet authorized'}}), 400

    user = User.query.get(qr.user_id)
    if not user:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'User not found'}}), 404

    qr.consumed = True
    qr.consumed_at = datetime.now(timezone.utc).replace(tzinfo=None)

    session_token = secrets.token_urlsafe(32)
    session['user_id'] = user.id
    session['username'] = user.username
    user.is_online = True
    user.last_seen = datetime.now(timezone.utc).replace(tzinfo=None)
    db.session.add(UserSession(
        user_id=user.id,
        session_token=session_token,
        device='K Web (QR Login)',
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        last_activity=datetime.now(timezone.utc).replace(tzinfo=None),
        is_active=True,
    ))
    db.session.commit()

    return jsonify({'success': True, 'data': {
        'user': {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'display_name': user.display_name or user.username,
            'avatar_url': user.avatar_url,
            'bio': getattr(user, 'bio', None),
            'is_premium': user.premium.is_premium if user.premium else False,
            'is_admin': getattr(user, 'is_admin', False),
            'is_online': True,
            'last_seen': datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            'created_at': user.created_at.isoformat() if user.created_at else datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        },
        'session_token': session_token,
    }})


# ── Shared: status (public) ────────────────────────────────────

@spav2_qr_bp.route('/status/<token>', methods=['GET'])
def qr_status(token):
    """Public: check if a token is consumed/expired/authorized."""
    qr = QrLoginToken.query.filter_by(token=token).first()
    if not qr:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Token not found'}}), 404

    expired = qr.expires_at < datetime.now(timezone.utc).replace(tzinfo=None)
    return jsonify({'success': True, 'data': {
        'consumed': qr.consumed,
        'expired': expired,
        'authorized': qr.user_id is not None,
        'consumed_at': qr.consumed_at.isoformat() if qr.consumed_at else None,
        'expires_at': qr.expires_at.isoformat(),
    }})
