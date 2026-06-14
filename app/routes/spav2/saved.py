from datetime import datetime
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import joinedload, selectinload
from app import db
from app.models import User, Message, Chat
from app.utils.helpers import get_current_user_id

spav2_saved_bp = Blueprint('spav2_saved', __name__, url_prefix='/api')


@spav2_saved_bp.route('/saved_messages', methods=['GET'])
def get_saved_messages():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 100)
    offset = (page - 1) * per_page

    query = Message.query.options(
        selectinload(Message.sender),
        selectinload(Message.chat)
    ).filter_by(receiver_id=current_user_id, is_saved=True)
    total = query.count()
    saved = query.order_by(Message.timestamp.desc()).offset(offset).limit(per_page).all()
    pages = (total + per_page - 1) // per_page if per_page else 0

    chat_ids = list(set(msg.chat_id for msg in saved if msg.chat_id))
    chats = {c.id: c for c in Chat.query.filter(Chat.id.in_(chat_ids)).all()} if chat_ids else {}

    result = []
    for msg in saved:
        sender = msg.sender
        chat_name = sender.username if sender else 'Unknown'
        chat = msg.chat if msg.chat_id else None
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
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': pages
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

    msg = Message.query.options(selectinload(Message.sender), selectinload(Message.chat)).get(message_id)
    if not msg:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Message not found'}}), 404

    if msg.is_saved:
        return jsonify({'success': False, 'error': {'code': 'ALREADY_SAVED', 'message': 'Message already saved'}}), 400

    msg.is_saved = True
    if hasattr(msg, 'saved_note'):
        msg.saved_note = data.get('note', '').strip() or None
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': 'Database error'}}), 500

    sender = msg.sender
    chat_name = sender.username if sender else 'Unknown'
    chat = msg.chat if msg.chat_id else None
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

    msg = Message.query.get(saved_id)
    if not msg:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Saved message not found'}}), 404
    if not msg.is_saved:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Saved message not found'}}), 404

    data = request.get_json() or {}
    msg.saved_note = data.get('note', '').strip() or None
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': 'Database error'}}), 500

    return jsonify({'success': True, 'data': {
        'saved_id': saved_id,
        'note': msg.saved_note,
        'updated_at': datetime.utcnow().isoformat()
    }})
