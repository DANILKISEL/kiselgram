# app/routes/spa/pins.py (create this file)

from flask import Blueprint, request, jsonify, session
from app import db
from app.models import PinnedChat
from app.utils.helpers import get_current_user_id

spa_pins_bp = Blueprint('spa_pins', __name__, url_prefix='/api')

@spa_pins_bp.route('/pin', methods=['POST'])
def pin_chat():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    data = request.get_json()
    chat_type = data.get('chat_type', 'personal')
    chat_id = data.get('chat_id')

    existing = PinnedChat.query.filter_by(user_id=user_id, chat_type=chat_type, chat_id=chat_id).first()
    if existing:
        return jsonify({'success': False, 'error': 'Already pinned'}), 400
    else:
        pin = PinnedChat(user_id=user_id, chat_type=chat_type, chat_id=chat_id)
        db.session.add(pin)
        db.session.commit()
        return jsonify({'success': True, 'pinned': True})

@spa_pins_bp.route('/unpin', methods=['POST'])
def unpin_chat():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    data = request.get_json()
    chat_type = data.get('chat_type', 'personal')
    chat_id = data.get('chat_id')

    pin = PinnedChat.query.filter_by(user_id=user_id, chat_type=chat_type, chat_id=chat_id).first()
    if pin:
        db.session.delete(pin)
        db.session.commit()
    return jsonify({'success': True, 'pinned': False})

@spa_pins_bp.route('/pinned', methods=['GET'])
def get_pinned_chats():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401

    pins = PinnedChat.query.filter_by(user_id=user_id).order_by(PinnedChat.pinned_at.desc()).all()
    result = []
    for pin in pins:
        result.append({
            'chat_type': pin.chat_type,
            'chat_id': pin.chat_id,
            'pinned_at': pin.pinned_at.isoformat()
        })
    return jsonify({'success': True, 'pinned': result})