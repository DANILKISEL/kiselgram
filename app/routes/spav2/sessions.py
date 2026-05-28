from flask import Blueprint, jsonify, session
from app import db
from app.models import UserSession, User
from app.utils.helpers import get_current_user_id

spav2_sessions_bp = Blueprint('spav2_sessions', __name__, url_prefix='/api')


@spav2_sessions_bp.route('/sessions', methods=['GET'])
def get_sessions():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    sessions = UserSession.query.filter_by(user_id=current_user_id).order_by(UserSession.last_activity.desc()).all()
    return jsonify({'success': True, 'data': {'sessions': [
        {
            'session_token': s.session_token,
            'device': s.device or 'Unknown device',
            'ip_address': s.ip_address,
            'is_current': s.session_token == session.get('session_token'),
            'last_active': s.last_activity.isoformat() if s.last_activity else None,
            'created_at': s.created_at.isoformat() if s.created_at else None
        }
        for s in sessions
    ]}})
