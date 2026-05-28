import os
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from app import db
from app.models import User
from app.utils.helpers import get_current_user

spav2_profile_bp = Blueprint('spav2_profile', __name__, url_prefix='/api')


@spav2_profile_bp.route('/profile', methods=['GET'])
def get_profile():
    current_user = get_current_user()
    if not current_user:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    return jsonify({'success': True, 'data': {
        'user_id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'display_name': current_user.display_name or current_user.username,
        'avatar_url': current_user.avatar_url,
        'bio': getattr(current_user, 'bio', None),
        'is_premium': getattr(current_user, 'is_premium', False) or (current_user.premium.is_premium if current_user.premium else False),
        'is_admin': getattr(current_user, 'is_admin', False),
        'is_online': getattr(current_user, 'is_online', False),
        'last_seen': current_user.last_seen.isoformat() if current_user.last_seen else None,
        'created_at': current_user.created_at.isoformat() if current_user.created_at else datetime.utcnow().isoformat()
    }})


@spav2_profile_bp.route('/profile', methods=['PUT'])
def update_profile():
    current_user = get_current_user()
    if not current_user:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    data = request.get_json() or {}
    if 'display_name' in data:
        current_user.display_name = data['display_name']
    if 'bio' in data:
        current_user.bio = data['bio']
    db.session.commit()
    return jsonify({'success': True, 'data': {'message': 'Profile updated'}})


@spav2_profile_bp.route('/profile/settings', methods=['GET'])
def get_settings():
    current_user = get_current_user()
    if not current_user:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    settings = getattr(current_user, 'settings', None)
    return jsonify({'success': True, 'data': {
        'theme': getattr(settings, 'theme', 'dark') if settings else 'dark',
        'font_size': getattr(settings, 'font_size', 'medium') if settings else 'medium',
        'colors': {
            'primary': getattr(settings, 'primary_color', '#4A90D9') if settings else '#4A90D9',
            'accent': getattr(settings, 'accent_color', '#F5A623') if settings else '#F5A623',
            'background': getattr(settings, 'background_color', '#1E1E2E') if settings else '#1E1E2E',
            'chat_bubble_self': getattr(settings, 'bubble_self_color', '#4A90D9') if settings else '#4A90D9',
            'chat_bubble_other': getattr(settings, 'bubble_other_color', '#2E2E3E') if settings else '#2E2E3E'
        }
    }})


@spav2_profile_bp.route('/profile/privacy', methods=['GET'])
def get_privacy():
    current_user = get_current_user()
    if not current_user:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    privacy = getattr(current_user, 'privacy_settings', None)
    return jsonify({'success': True, 'data': {
        'last_seen': getattr(privacy, 'last_seen', 'contacts_only') if privacy else 'contacts_only',
        'profile_photo': getattr(privacy, 'profile_photo', 'everyone') if privacy else 'everyone',
        'calls': getattr(privacy, 'calls', 'contacts_only') if privacy else 'contacts_only',
        'messages': getattr(privacy, 'messages', 'everyone') if privacy else 'everyone'
    }})


@spav2_profile_bp.route('/profile/avatar', methods=['POST'])
def upload_avatar():
    current_user = get_current_user()
    if not current_user:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    if 'avatar' not in request.files:
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Avatar must be a JPEG or PNG under 5MB'}}), 400

    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'No file selected'}}), 400

    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
    filename = f"avatar_{current_user.id}_{os.urandom(4).hex()}.{ext}"
    upload_dir = os.path.join('uploads', 'avatars')
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, filename))

    current_user.avatar_url = f"/uploads/avatars/{filename}"
    db.session.commit()

    return jsonify({'success': True, 'data': {
        'user_id': current_user.id,
        'avatar_url': current_user.avatar_url,
        'updated_at': datetime.utcnow().isoformat()
    }})
