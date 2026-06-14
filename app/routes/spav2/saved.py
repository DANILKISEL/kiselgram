from datetime import datetime
from flask import Blueprint, request, jsonify
from app import db
from app.models import User, Message, Chat
from app.utils.helpers import get_current_user_id

spav2_saved_bp = Blueprint('spav2_saved', __name__, url_prefix='/api')


@spav2_saved_bp.route('/saved_messages', methods=['GET'])
def get_saved_messages():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    after_id = request.args.get('after', 0, type=int)
    limit = min(request.args.get('limit', 50, type=int), 100)

    saved = Message.query.filter_by(receiver_id=current_user_id, is_saved=True).filter(Message.id > after_id).order_by(Message.timestamp.desc()).limit(limit).all()
    has_more = len(saved) == limit
    next_cursor = saved[-1].id if saved else None

    sender_ids = list(set(msg.sender_id for msg in saved))
    senders = {u.id: u for u in User.query.filter(User.id.in_(sender_ids)).all()} if sender_ids else {}
    result = []
    for msg in saved:
        sender = senders.get(msg.sender_id)
        chat_name = sender.username if sender else 'Unknown'
        chat = Chat.query.get(msg.chat_id) if msg.chat_id else None
        if chat:
            chat_name = chat.name
        chat_type = 'group' if msg.chat_id else 'personal'

        result.append({
            'saved_id': msg.id,
            'original_message': {
                'message_id': msg.id,
                'sender_id': msg.sender_id,
                'sender_username': sender.username if sender else None,
                'content': msg.content,
                'chat_type': chat_type,
                'chat_name': chat_name,
                'timestamp': msg.timestamp.isoformat() if msg.timestamp else None
            },
            'saved_at': msg.timestamp.isoformat() if msg.timestamp else None,
            'note': getattr(msg, 'saved_note', None)
        })

    return jsonify({'success': True, 'data': {
        'messages': result,
        'pagination': {'after': after_id or None, 'limit': limit, 'has_more': has_more, 'next_cursor': next_cursor}
    }})


@spav2_saved_bp.route('/saved_messages', methods=['POST'])
def save_message():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    data = request.get_json() or {}
    message_id = data.get('message_id')

    if not message_id:
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'message_id is required'}}), 400

    msg = Message.query.get(message_id)
    if not msg:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Message not found'}}), 404

    if msg.is_saved:
        return jsonify({'success': False, 'error': {'code': 'ALREADY_SAVED', 'message': 'Message already saved'}}), 400

    msg.is_saved = True
    if hasattr(msg, 'saved_note'):
        msg.saved_note = data.get('note', '').strip() or None
    db.session.commit()

    sender = User.query.get(msg.sender_id)
    chat_name = sender.username if sender else 'Unknown'
    from app.models import Chat
    chat = Chat.query.get(msg.chat_id) if msg.chat_id else None
    if chat:
        chat_name = chat.name
    chat_type = 'group' if msg.chat_id else 'personal'

    return jsonify({'success': True, 'data': {
        'saved_id': msg.id,
        'original_message': {
            'message_id': msg.id,
            'sender_id': msg.sender_id,
            'sender_username': sender.username if sender else None,
            'content': msg.content,
            'chat_type': chat_type,
            'chat_name': chat_name,
            'timestamp': msg.timestamp.isoformat() if msg.timestamp else None
        },
        'saved_at': datetime.utcnow().isoformat(),
        'note': getattr(msg, 'saved_note', None)
    }}), 201


@spav2_saved_bp.route('/saved_messages/<int:saved_id>/note', methods=['POST'])
def update_saved_note(saved_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    msg = Message.query.get_or_404(saved_id)
    if not hasattr(msg, 'saved_note'):
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Saved message not found'}}), 404

    data = request.get_json() or {}
    msg.saved_note = data.get('note', '').strip() or None
    db.session.commit()

    return jsonify({'success': True, 'data': {
        'saved_id': saved_id,
        'note': msg.saved_note,
        'updated_at': datetime.utcnow().isoformat()
    }})
