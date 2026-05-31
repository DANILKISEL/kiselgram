import time
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from app import db
from app.models import User, Message, Reaction, Reply, Forward, BlockedUser, Chat, ChatMember, File
from app.utils.helpers import get_current_user_id, message_to_dict

spav2_messages_bp = Blueprint('spav2_messages', __name__, url_prefix='/api')

_typing_status = {}
_TYPING_TIMEOUT = 5


def _serialize_message(msg, current_user_id=None):
    from app.models import Reaction as ReactionModel
    d = {
        'message_id': msg.id,
        'sender_id': msg.sender_id,
        'receiver_id': msg.receiver_id,
        'content': msg.content,
        'reply_to_id': None,
        'file_path': msg.file_path,
        'file_url': f"/uploads/{msg.file_path}" if msg.file_path else None,
        'file_type': msg.file_type,
        'is_read': msg.is_read,
        'timestamp': msg.timestamp.isoformat() if msg.timestamp else None,
        'edited_at': msg.edited_at.isoformat() if msg.edited_at else None,
        'reactions': {}
    }
    if msg.sender:
        d['sender_username'] = msg.sender.username
        d['sender_avatar_url'] = msg.sender.avatar_url
    if msg.reply_to:
        d['reply_to_id'] = msg.reply_to.id
    reactions = ReactionModel.query.filter_by(message_id=msg.id).all()
    for r in reactions:
        d['reactions'][r.reaction_type] = d['reactions'].get(r.reaction_type, 0) + 1
    return d


@spav2_messages_bp.route('/send_message', methods=['POST'])
def send_personal_message():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    data = request.get_json() or {}
    receiver_id = data.get('receiver_id')
    content = data.get('content', '').strip()
    reply_to_id = data.get('reply_to_id')

    errors = {}
    if not receiver_id:
        errors['receiver_id'] = 'Receiver ID is required'
    if not content:
        errors['content'] = 'Message content cannot be empty'
    if errors:
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Validation failed', 'fields': errors}}), 400

    if BlockedUser.query.filter_by(user_id=receiver_id, blocked_user_id=current_user_id).first():
        return jsonify({'success': False, 'error': {'code': 'USER_BLOCKED', 'message': 'You cannot send messages to this user'}}), 403

    receiver = User.query.get(receiver_id)
    if not receiver:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'User not found'}}), 404

    a, b = sorted([current_user_id, receiver_id])
    chat = Chat.query.filter_by(chat_type='personal', user1_id=a, user2_id=b).first()
    if not chat:
        chat = Chat(chat_type='personal', user1_id=a, user2_id=b)
        db.session.add(chat)
        db.session.flush()

    msg = Message(content=content, sender_id=current_user_id, receiver_id=receiver_id, chat_id=chat.id, timestamp=datetime.utcnow())
    db.session.add(msg)
    db.session.flush()

    if reply_to_id:
        original = Message.query.get(reply_to_id)
        if original:
            db.session.add(Reply(original_message_id=reply_to_id, reply_message_id=msg.id))

    db.session.commit()
    return jsonify({'success': True, 'data': {'message': _serialize_message(msg, current_user_id)}}), 201


@spav2_messages_bp.route('/mark_read/<int:user_id>', methods=['POST'])
def mark_read(user_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    count = Message.query.filter_by(sender_id=user_id, receiver_id=current_user_id, is_read=False).update({'is_read': True, 'read_at': datetime.utcnow()})
    db.session.commit()
    return jsonify({'success': True, 'data': {'marked_count': count, 'peer_user_id': user_id}})


@spav2_messages_bp.route('/messages/<int:message_id>/edit', methods=['POST'])
def edit_message(message_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    msg = Message.query.get_or_404(message_id)
    if msg.sender_id != current_user_id:
        return jsonify({'success': False, 'error': {'code': 'FORBIDDEN', 'message': 'You can only edit your own messages'}}), 403

    data = request.get_json() or {}
    content = data.get('content', '').strip()
    if not content:
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Content cannot be empty'}}), 400

    msg.content = content
    msg.edited_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True, 'data': {'message': _serialize_message(msg, current_user_id)}})


@spav2_messages_bp.route('/typing/<chat_type>/<int:chat_id>', methods=['POST'])
def set_typing(chat_type, chat_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    key = f"{chat_type}_{chat_id}"
    if key not in _typing_status:
        _typing_status[key] = {}
    _typing_status[key][current_user_id] = time.time()

    expires_at = datetime.utcfromtimestamp(time.time() + _TYPING_TIMEOUT).isoformat()
    return jsonify({'success': True, 'data': {
        'chat_type': chat_type,
        'chat_id': str(chat_id),
        'is_typing': True,
        'expires_at': expires_at
    }})


@spav2_messages_bp.route('/reactions/add', methods=['POST'])
def add_reaction():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    data = request.get_json() or {}
    message_id = data.get('message_id')
    reaction_type = data.get('reaction_type')

    if not reaction_type or not reaction_type.strip():
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Reaction type is required'}}), 400
    reaction_type = reaction_type.strip()

    existing = Reaction.query.filter_by(message_id=message_id, user_id=current_user_id, reaction_type=reaction_type).first()
    if existing:
        db.session.delete(existing)
        has_reacted = False
    else:
        db.session.add(Reaction(message_id=message_id, user_id=current_user_id, reaction_type=reaction_type))
        has_reacted = True
    db.session.commit()

    count = Reaction.query.filter_by(message_id=message_id, reaction_type=reaction_type).count()
    return jsonify({'success': True, 'data': {
        'message_id': message_id,
        'reaction_type': reaction_type,
        'has_reacted': has_reacted,
        'reaction_count': count
    }})


@spav2_messages_bp.route('/messages/<int:message_id>/delete', methods=['POST'])
def delete_message(message_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    msg = Message.query.get_or_404(message_id)
    if msg.sender_id != current_user_id:
        return jsonify({'success': False, 'error': {'code': 'FORBIDDEN', 'message': 'You can only delete your own messages'}}), 403

    msg.is_deleted = True
    db.session.commit()
    return jsonify({'success': True, 'data': {'message_id': message_id}})


@spav2_messages_bp.route('/reactions/<int:message_id>', methods=['GET'])
def get_reactions(message_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    reactions = Reaction.query.filter_by(message_id=message_id).all()
    grouped = {}
    for r in reactions:
        if r.reaction_type not in grouped:
            grouped[r.reaction_type] = []
        grouped[r.reaction_type].append({'user_id': r.user_id, 'username': r.user.username if r.user else None})

    result = []
    for rtype, users in grouped.items():
        has_reacted = any(u['user_id'] == current_user_id for u in users)
        result.append({
            'reaction_type': rtype,
            'count': len(users),
            'users': users,
            'has_reacted': has_reacted
        })

    return jsonify({'success': True, 'data': {'message_id': message_id, 'reactions': result}})
