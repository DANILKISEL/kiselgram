import secrets
import re
from flask import Blueprint, request, jsonify, session
from datetime import datetime
from app import db
from app.models import User, Message, Chat, ChatMember, ChatSubscriber, PinnedChat, BlockedUser
from app.utils.helpers import get_current_user_id, get_blocked_user_ids, has_active_story
from app.utils.security import sanitize_string

spav2_chat_bp = Blueprint('spav2_chat', __name__, url_prefix='/api')


def _serialize_peer(user):
    return {
        'user_id': user.id,
        'username': user.username,
        'display_name': user.display_name or user.username,
        'avatar_url': user.avatar_url,
        'is_online': getattr(user, 'is_online', False),
        'last_seen': user.last_seen.isoformat() if user.last_seen else None,
        'status_emoji': getattr(user, 'status_emoji', '') or '',
        'is_bot': getattr(user, 'is_bot', False),
        'bot_webapp_url': getattr(user, 'bot_webapp_url', None) or None
    }


def _serialize_message(msg, current_user_id):
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
    reactions = ReactionModel.query.filter_by(message_id=msg.id).all()
    for r in reactions:
        d['reactions'][r.reaction_type] = d['reactions'].get(r.reaction_type, 0) + 1
    return d


@spav2_chat_bp.route('/chat_list', methods=['GET'])
def chat_list():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    blocked_ids = get_blocked_user_ids(current_user_id)
    chats = []

    # Personal chats
    sent = db.session.query(Message.receiver_id).filter_by(sender_id=current_user_id).distinct().all()
    recv = db.session.query(Message.sender_id).filter_by(receiver_id=current_user_id).distinct().all()
    chat_user_ids = set([r[0] for r in sent] + [r[0] for r in recv])

    for uid in chat_user_ids:
        if uid in blocked_ids or uid == current_user_id:
            continue
        user = User.query.get(uid)
        if not user:
            continue
        last = Message.query.filter(
            ((Message.sender_id == current_user_id) & (Message.receiver_id == uid)) |
            ((Message.sender_id == uid) & (Message.receiver_id == current_user_id))
        ).order_by(Message.timestamp.desc()).first()

        unread = Message.query.filter_by(sender_id=uid, receiver_id=current_user_id, is_read=False).count()

        chats.append({
            'chat_type': 'personal',
            'peer': _serialize_peer(user),
            'last_message': {
                'message_id': last.id,
                'content': last.content,
                'sender_id': last.sender_id,
                'timestamp': last.timestamp.isoformat() if last.timestamp else None,
                'is_read': last.is_read
            } if last else None,
            'unread_count': unread
        })

    # Groups
    memberships = ChatMember.query.filter_by(user_id=current_user_id).all()
    for m in memberships:
        chat = Chat.query.get(m.chat_id)
        if not chat:
            continue
        last = Message.query.filter_by(chat_id=chat.id).order_by(Message.timestamp.desc()).first()
        unread = Message.query.filter_by(chat_id=chat.id, is_read=False).filter(Message.sender_id != current_user_id).count() if last else 0

        chats.append({
            'chat_type': 'group',
            'group': {
                'group_id': chat.id,
                'name': chat.name,
                'avatar_url': chat.avatar_url
            },
            'last_message': {
                'message_id': last.id,
                'content': last.content,
                'sender_id': last.sender_id,
                'sender_username': last.sender.username if last.sender else None,
                'timestamp': last.timestamp.isoformat() if last.timestamp else None
            } if last else None,
            'unread_count': unread
        })

    # Channels
    subscriptions = ChatSubscriber.query.filter_by(user_id=current_user_id).all()
    for s in subscriptions:
        chat = Chat.query.get(s.chat_id)
        if not chat:
            continue
        last = Message.query.filter_by(chat_id=chat.id).order_by(Message.timestamp.desc()).first()

        chats.append({
            'chat_type': 'channel',
            'channel': {
                'channel_id': chat.id,
                'name': chat.name,
                'avatar_url': chat.avatar_url
            },
            'last_message': {
                'message_id': last.id,
                'content': last.content,
                'timestamp': last.timestamp.isoformat() if last.timestamp else None
            } if last else None,
            'unread_count': 0
        })

    return jsonify({'success': True, 'data': {'chats': chats}})


@spav2_chat_bp.route('/messages/<int:user_id>', methods=['GET'])
def get_personal_messages(user_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    if BlockedUser.query.filter_by(user_id=user_id, blocked_user_id=current_user_id).first():
        return jsonify({'success': False, 'error': {'code': 'BLOCKED', 'message': 'You are blocked by this user'}}), 403

    after_id = request.args.get('after', 0, type=int)
    limit = min(request.args.get('limit', 50, type=int), 100)

    peer = User.query.get(user_id)
    if not peer:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'User not found'}}), 404

    messages = Message.query.filter(
        ((Message.sender_id == current_user_id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user_id))
    ).filter(Message.id > after_id).order_by(Message.timestamp.asc()).limit(limit).all()

    has_more = len(messages) == limit
    next_cursor = messages[-1].id if messages else None

    return jsonify({'success': True, 'data': {
        'peer': _serialize_peer(peer),
        'messages': [_serialize_message(m, current_user_id) for m in messages],
        'pagination': {
            'after': after_id if after_id else None,
            'limit': limit,
            'has_more': has_more,
            'next_cursor': next_cursor
        }
    }})


@spav2_chat_bp.route('/typing/<chat_type>/<int:chat_id>', methods=['GET'])
def get_typing(chat_type, chat_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401
    from .messages import _typing_status, _TYPING_TIMEOUT
    import time
    key = f"{chat_type}_{chat_id}"
    now = time.time()
    typists = []
    if key in _typing_status:
        expired = []
        for uid, ts in _typing_status[key].items():
            if now - ts > _TYPING_TIMEOUT:
                expired.append(uid)
            elif uid != current_user_id:
                user = User.query.get(uid)
                if user:
                    typists.append({
                        'user_id': uid,
                        'username': user.username,
                        'started_at': datetime.fromtimestamp(ts).isoformat()
                    })
        for uid in expired:
            del _typing_status[key][uid]
        if not _typing_status[key]:
            del _typing_status[key]
    return jsonify({'success': True, 'data': {'typing_users': typists}})

@spav2_chat_bp.route('/bot/<int:bot_id>/webapp', methods=['GET'])
def get_bot_webapp(bot_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED'}}), 401
    bot = User.query.get(bot_id)
    if not bot or not bot.is_bot:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND'}}), 404
    return jsonify({'success': True, 'data': {'bot_id': bot_id, 'webapp_url': bot.bot_webapp_url or None}})

@spav2_chat_bp.route('/bot/<int:bot_id>/webapp', methods=['PUT'])
def update_bot_webapp(bot_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED'}}), 401
    bot = User.query.get(bot_id)
    if not bot or not bot.is_bot or bot.bot_owner_id != current_user_id:
        return jsonify({'success': False, 'error': {'code': 'FORBIDDEN'}}), 403
    data = request.get_json() or {}
    url = data.get('webapp_url', '').strip()
    if url and not url.startswith('https://'):
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Only HTTPS URLs allowed'}}), 400
    bot.bot_webapp_url = url or None
    db.session.commit()
    return jsonify({'success': True, 'data': {'bot_id': bot_id, 'webapp_url': bot.bot_webapp_url}})

@spav2_chat_bp.route('/bots', methods=['GET', 'POST'])
def handle_bots():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED'}}), 401

    if request.method == 'GET':
        bots = User.query.filter_by(bot_owner_id=current_user_id, is_bot=True).all()
        return jsonify({'success': True, 'data': {'bots': [{
            'bot_id': b.id,
            'username': b.username,
            'display_name': b.display_name or b.username,
            'avatar_url': b.avatar_url,
            'bot_webapp_url': b.bot_webapp_url or None
        } for b in bots]}})

    # POST — create a new bot
    data = request.get_json() or {}
    username = sanitize_string(data.get('username', ''), max_length=32).lower()
    display_name = sanitize_string(data.get('display_name', ''), max_length=64) or username

    errors = {}
    if len(username) < 3 or not re.match(r'^[a-zA-Z0-9_]+$', username):
        errors['username'] = 'Username must be 3-32 characters (letters, numbers, underscores)'
    if User.query.filter_by(username=username).first():
        errors['username'] = 'Username already taken'
    if errors:
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Validation failed', 'fields': errors}}), 400

    bot_token = secrets.token_urlsafe(48)
    bot = User(
        username=username,
        display_name=display_name,
        email=None,
        is_bot=True,
        bot_owner_id=current_user_id,
        bot_token=bot_token,
        is_online=False,
        last_seen=datetime.utcnow()
    )
    bot.set_password(secrets.token_urlsafe(24))
    db.session.add(bot)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'SERVER_ERROR', 'message': str(e)}}), 500

    return jsonify({'success': True, 'data': {
        'bot_id': bot.id,
        'username': bot.username,
        'display_name': bot.display_name,
        'bot_token': bot_token,
        'message': 'Bot created. Save the token — it is shown only once.'
    }}), 201
