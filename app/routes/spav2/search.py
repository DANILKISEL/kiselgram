from datetime import datetime
from flask import Blueprint, request, jsonify, session
from app import db
from app.models import User, Chat, ChatMember, Contact, BlockedUser, Message
from app.utils.helpers import get_current_user_id, get_current_user

spav2_search_bp = Blueprint('spav2_search', __name__, url_prefix='/api')


@spav2_search_bp.route('/search/global', methods=['GET'])
def global_search():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Query must be at least 2 characters'}}), 400

    q = f"%{query}%"
    blocked_ids = [b.blocked_user_id for b in BlockedUser.query.filter_by(user_id=current_user_id).all()]

    # Users
    users = User.query.filter(User.username.ilike(q) | (User.display_name.ilike(q))).limit(10).all()
    contacts_set = set(c.contact_id for c in Contact.query.filter_by(user_id=current_user_id).all())
    users_data = []
    for u in users:
        if u.id == current_user_id or u.id in blocked_ids:
            continue
        users_data.append({
            'user_id': u.id,
            'username': u.username,
            'display_name': u.display_name or u.username,
            'avatar_url': u.avatar_url,
            'is_contact': u.id in contacts_set
        })

    # Groups
    memberships = ChatMember.query.filter_by(user_id=current_user_id).all()
    group_ids = set(m.chat_id for m in memberships)
    groups = Chat.query.filter(Chat.id.in_(group_ids), Chat.name.ilike(q), Chat.chat_type == 'group').limit(10).all()
    groups_data = []
    for g in groups:
        groups_data.append({
            'group_id': g.id,
            'name': g.name,
            'avatar_url': g.avatar_url,
            'member_count': ChatMember.query.filter_by(chat_id=g.id).count(),
            'is_member': True
        })

    # Channels
    from app.models import ChatSubscriber
    subs = ChatSubscriber.query.filter_by(user_id=current_user_id).all()
    chan_ids = set(s.chat_id for s in subs)
    channels = Chat.query.filter(Chat.id.in_(chan_ids), Chat.name.ilike(q), Chat.chat_type == 'channel').limit(10).all()
    channels_data = []
    for c in channels:
        channels_data.append({
            'channel_id': c.id,
            'name': c.name,
            'avatar_url': c.avatar_url,
            'subscriber_count': ChatSubscriber.query.filter_by(chat_id=c.id).count(),
            'is_subscribed': True
        })

    return jsonify({'success': True, 'data': {
        'query': query,
        'results': {
            'users': users_data,
            'groups': groups_data,
            'channels': channels_data
        }
    }})


@spav2_search_bp.route('/users', methods=['GET'])
def search_users():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    query = request.args.get('search', '').strip()
    if not query or len(query) < 2:
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Search query must be at least 2 characters'}}), 400

    q = f"%{query}%"
    blocked_ids = [b.blocked_user_id for b in BlockedUser.query.filter_by(user_id=current_user_id).all()]
    contacts_set = set(c.contact_id for c in Contact.query.filter_by(user_id=current_user_id).all())

    users = User.query.filter(User.username.ilike(q) | (User.display_name.ilike(q))).limit(20).all()
    result = []
    for u in users:
        if u.id == current_user_id or u.id in blocked_ids:
            continue
        result.append({
            'user_id': u.id,
            'username': u.username,
            'display_name': u.display_name or u.username,
            'avatar_url': u.avatar_url,
            'bio': getattr(u, 'bio', None),
            'is_online': getattr(u, 'is_online', False),
            'is_contact': u.id in contacts_set
        })

    return jsonify({'success': True, 'data': {'query': query, 'users': result, 'total': len(result)}})


@spav2_search_bp.route('/search_in_chat', methods=['POST'])
def search_in_chat():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    data = request.get_json() or {}
    chat_id = data.get('chat_id')
    query = data.get('query', '').strip()

    if not chat_id or not query:
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'chat_id and query are required'}}), 400

    chat_type = data.get('chat_type', 'personal')
    q = f"%{query}%"

    if chat_type == 'personal':
        messages = Message.query.filter(
            ((Message.sender_id == current_user_id) & (Message.receiver_id == int(chat_id))) |
            ((Message.sender_id == int(chat_id)) & (Message.receiver_id == current_user_id)),
            Message.content.ilike(q)
        ).order_by(Message.timestamp.desc()).limit(50).all()
    else:
        messages = Message.query.filter_by(chat_id=int(chat_id)).filter(Message.content.ilike(q)).order_by(Message.timestamp.desc()).limit(50).all()

    results = []
    for msg in messages:
        results.append({
            'message_id': msg.id,
            'sender_id': msg.sender_id,
            'content': msg.content,
            'timestamp': msg.timestamp.isoformat() if msg.timestamp else None
        })

    return jsonify({'success': True, 'data': {
        'chat_id': chat_id, 'chat_type': chat_type,
        'query': query, 'results': results, 'total': len(results)
    }})


@spav2_search_bp.route('/recent_searches', methods=['GET'])
def recent_searches():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    from app.models import RecentSearch
    searches = RecentSearch.query.filter_by(user_id=current_user_id).order_by(RecentSearch.created_at.desc()).limit(10).all()
    return jsonify({'success': True, 'data': {'searches': [
        {'search_id': s.id, 'query': s.query, 'created_at': s.created_at.isoformat() if s.created_at else None}
        for s in searches
    ]}})


@spav2_search_bp.route('/recent_searches', methods=['POST'])
def add_recent_search():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    data = request.get_json() or {}
    query = data.get('query', '').strip()
    if not query:
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'query is required'}}), 400

    from app.models import RecentSearch
    existing = RecentSearch.query.filter_by(user_id=current_user_id, query=query).first()
    if existing:
        existing.created_at = datetime.utcnow()
    else:
        db.session.add(RecentSearch(user_id=current_user_id, query=query, created_at=datetime.utcnow()))

    RecentSearch.query.filter_by(user_id=current_user_id).order_by(RecentSearch.created_at.desc()).offset(20).delete()
    db.session.commit()
    return jsonify({'success': True, 'data': {'message': 'Search saved'}})
