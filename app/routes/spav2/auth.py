from flask import Blueprint, request, jsonify, session
from datetime import datetime
import re
import secrets
from app import db
from app.models import User, EmailVerification, UserSession
from app.utils.helpers import get_current_user

spav2_auth_bp = Blueprint('spav2_auth', __name__, url_prefix='/api/auth')

@spav2_auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    errors = {}
    if len(username) < 3 or not re.match(r'^[a-zA-Z0-9_]+$', username):
        errors['username'] = 'Username must be at least 3 characters (letters, numbers, underscores)'
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        errors['email'] = 'Invalid email format'
    if len(password) < 8:
        errors['password'] = 'Password must be at least 8 characters'
    if User.query.filter_by(username=username).first():
        errors['username'] = 'Username already taken'
    if User.query.filter_by(email=email).first():
        errors['email'] = 'Email already registered'
    if errors:
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Validation failed', 'fields': errors}}), 400

    user = User(username=username, email=email, display_name=username, is_online=True, last_seen=datetime.utcnow())
    user.set_password(password)
    user.email_verified = True
    db.session.add(user)
    db.session.flush()

    session_token = secrets.token_urlsafe(32)
    session['user_id'] = user.id
    session['username'] = user.username
    db.session.add(UserSession(user_id=user.id, session_token=session_token, device='K Web', created_at=datetime.utcnow(), last_activity=datetime.utcnow(), is_active=True))
    db.session.commit()

    return jsonify({'success': True, 'data': {
        'user': {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'display_name': user.display_name,
            'avatar_url': user.avatar_url,
            'bio': getattr(user, 'bio', None),
            'is_premium': getattr(user, 'is_premium', False) or (user.premium.is_premium if user.premium else False),
            'is_admin': getattr(user, 'is_admin', False),
            'is_online': True,
            'last_seen': datetime.utcnow().isoformat(),
            'created_at': user.created_at.isoformat() if user.created_at else datetime.utcnow().isoformat()
        },
        'session_token': session_token
    }}), 201


@spav2_auth_bp.route('login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'success': False, 'error': {'code': 'INVALID_CREDENTIALS', 'message': 'Invalid username or password'}}), 401

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({'success': False, 'error': {'code': 'INVALID_CREDENTIALS', 'message': 'Invalid username or password'}}), 401

    session_token = secrets.token_urlsafe(32)
    session['user_id'] = user.id
    session['username'] = user.username
    user.is_online = True
    user.last_seen = datetime.utcnow()
    db.session.add(UserSession(user_id=user.id, session_token=session_token, device='K Web', created_at=datetime.utcnow(), last_activity=datetime.utcnow(), is_active=True))
    db.session.commit()

    return jsonify({'success': True, 'data': {
        'user': {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'display_name': user.display_name or user.username,
            'avatar_url': user.avatar_url,
            'bio': getattr(user, 'bio', None),
            'is_premium': getattr(user, 'is_premium', False) or (user.premium.is_premium if user.premium else False),
            'is_admin': getattr(user, 'is_admin', False),
            'is_online': True,
            'last_seen': datetime.utcnow().isoformat(),
            'created_at': user.created_at.isoformat() if user.created_at else datetime.utcnow().isoformat()
        },
        'session_token': session_token
    }})


@spav2_auth_bp.route('logout', methods=['POST'])
def logout():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        if user:
            user.is_online = False
            user.last_seen = datetime.utcnow()
            db.session.commit()
    session.clear()
    return jsonify({'success': True, 'data': {'message': 'Logged out successfully'}})


@spav2_auth_bp.route('/check_username', methods=['GET'])
def check_username():
    username = request.args.get('username', '').strip()
    if not username:
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Username is required'}}), 400
    user_id = session.get('user_id')
    existing = User.query.filter_by(username=username).first()
    available = existing is None or (user_id and existing.id == user_id)
    return jsonify({'success': True, 'data': {'username': username, 'available': available}})
