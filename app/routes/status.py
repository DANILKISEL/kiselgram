from flask import Blueprint, jsonify
from app import db
from app.models import Message, User
from app.utils import get_current_user, get_current_user_id

status_bp = Blueprint('status', __name__)


@status_bp.route('/api/user_status/<int:user_id>')
def user_status(user_id):
    if not get_current_user():
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Check if user is online (simplified - always return online for now)
    return jsonify({
        'user_id': user.id,
        'username': user.username,
        'is_online': True,
        'last_seen': None
    })


@status_bp.route('/api/mark_read/<int:user_id>', methods=['POST'])
def mark_read(user_id):
    if not get_current_user():
        return jsonify({'error': 'Not authenticated'}), 401

    current_user_id = get_current_user_id()

    # Mark all messages from this user as read
    Message.query.filter_by(
        sender_id=user_id,
        receiver_id=current_user_id,
        is_read=False
    ).update({'is_read': True})

    db.session.commit()

    return jsonify({'success': True})