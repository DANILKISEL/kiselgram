import os
import json
import secrets
from datetime import datetime
from flask import Blueprint, request, jsonify
from app import db
from app.models import User, Chat, ChatMember, GroupPermission, Message, File
from app.utils.helpers import get_current_user_id

spav2_groups_bp = Blueprint('spav2_groups', __name__, url_prefix='/api')


def _serialize_group(chat, member_count=None):
    if member_count is None:
        member_count = ChatMember.query.filter_by(chat_id=chat.id).count()
    last = Message.query.filter_by(chat_id=chat.id).order_by(Message.timestamp.desc()).first()
    return {
        'group_id': chat.id,
        'name': chat.name,
        'description': chat.description,
        'avatar_url': chat.avatar_url,
        'owner_id': chat.owner_id,
        'is_public': chat.is_public,
        'invite_link': f"kiselgram.com/join/{chat.invite_link}" if chat.invite_link else None,
        'member_count': member_count,
        'my_role': None,
        'last_message': {
            'message_id': last.id,
            'content': last.content,
            'sender_username': last.sender.username if last.sender else None,
            'timestamp': last.timestamp.isoformat() if last.timestamp else None
        } if last else None,
        'created_at': chat.created_at.isoformat() if chat.created_at else None
    }


@spav2_groups_bp.route('/groups', methods=['GET'])
def get_groups():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    memberships = ChatMember.query.filter_by(user_id=current_user_id).all()
    chat_ids = [m.chat_id for m in memberships]
    chats_map = {c.id: c for c in Chat.query.filter(Chat.id.in_(chat_ids)).all()} if chat_ids else {}
    counts = dict(db.session.query(ChatMember.chat_id, db.func.count(ChatMember.id)).filter(ChatMember.chat_id.in_(chat_ids)).group_by(ChatMember.chat_id).all()) if chat_ids else {}
    groups = []
    for m in memberships:
        chat = chats_map.get(m.chat_id)
        if chat:
            g = _serialize_group(chat, member_count=counts.get(chat.id, 0))
            g['my_role'] = m.role
            groups.append(g)

    return jsonify({'success': True, 'data': {'groups': groups}})


@spav2_groups_bp.route('/groups/<int:group_id>', methods=['GET'])
def get_group(group_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    chat = Chat.query.get(group_id)
    if not chat or chat.chat_type != 'group':
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Group not found'}}), 404

    membership = ChatMember.query.filter_by(user_id=current_user_id, chat_id=group_id).first()
    if not membership and not chat.is_public:
        return jsonify({'success': False, 'error': {'code': 'FORBIDDEN', 'message': 'You are not a member'}}), 403

    owner = User.query.get(chat.owner_id)
    return jsonify({'success': True, 'data': {
        'group_id': chat.id,
        'name': chat.name,
        'description': chat.description,
        'avatar_url': chat.avatar_url,
        'owner_id': chat.owner_id,
        'owner_username': owner.username if owner else None,
        'is_public': chat.is_public,
        'invite_link': f"kiselgram.com/join/{chat.invite_link}" if chat.invite_link else None,
        'created_at': chat.created_at.isoformat() if chat.created_at else None,
        'member_count': ChatMember.query.filter_by(chat_id=chat.id).count(),
        'members_url': f"/api/groups/{group_id}/members"
    }})


@spav2_groups_bp.route('/groups/<int:group_id>/members', methods=['GET'])
def get_group_members(group_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    offset = request.args.get('offset', 0, type=int)
    limit = min(request.args.get('limit', 50, type=int), 100)

    memberships = ChatMember.query.filter_by(chat_id=group_id).offset(offset).limit(limit).all()
    total = ChatMember.query.filter_by(chat_id=group_id).count()
    members = []
    for m in memberships:
        user = User.query.get(m.user_id)
        if user:
            members.append({
                'user_id': user.id,
                'username': user.username,
                'avatar_url': user.avatar_url,
                'role': m.role,
                'joined_at': m.joined_at.isoformat() if m.joined_at else None
            })

    return jsonify({'success': True, 'data': {
        'group_id': group_id,
        'members': members,
        'pagination': {'offset': offset, 'limit': limit, 'has_more': len(members) == limit, 'total': total}
    }})


@spav2_groups_bp.route('/group_messages/<int:group_id>', methods=['GET'])
def get_group_messages(group_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    if not ChatMember.query.filter_by(user_id=current_user_id, chat_id=group_id).first():
        return jsonify({'success': False, 'error': {'code': 'NOT_MEMBER', 'message': 'Not a member'}}), 403

    after_id = request.args.get('after', 0, type=int)
    limit = min(request.args.get('limit', 50, type=int), 100)

    messages = Message.query.options(db.joinedload(Message.reactions)).filter_by(chat_id=group_id).filter(Message.id > after_id).order_by(Message.timestamp.asc()).limit(limit).all()
    has_more = len(messages) == limit

    result = []
    for msg in messages:
        reacs = {}
        for r in msg.reactions:
            reacs[r.reaction_type] = reacs.get(r.reaction_type, 0) + 1
        d = {
            'message_id': msg.id,
            'sender_id': msg.sender_id,
            'sender_username': msg.sender.username if msg.sender else None,
            'sender_avatar_url': msg.sender.avatar_url if msg.sender else None,
            'content': msg.content,
            'reply_to_id': None,
            'file_path': msg.file_path,
            'file_type': msg.file_type,
            'timestamp': msg.timestamp.isoformat() if msg.timestamp else None,
            'edited_at': msg.edited_at.isoformat() if msg.edited_at else None,
            'reactions': reacs
        }
        result.append(d)

    next_cursor = messages[-1].id if messages else None
    return jsonify({'success': True, 'data': {
        'group_id': group_id,
        'messages': result,
        'pagination': {'after': after_id or None, 'limit': limit, 'has_more': has_more, 'next_cursor': next_cursor}
    }})


@spav2_groups_bp.route('/groups/create', methods=['POST'])
def create_group():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    data = request.get_json() or {}
    name = data.get('name', '').strip()
    description = data.get('description', '')
    member_ids = data.get('member_ids', [])

    if not name:
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Validation failed', 'fields': {'name': 'Group name is required', 'member_ids': 'At least one member is required'}}}), 400

    invite_link = secrets.token_urlsafe(16)
    chat = Chat(chat_type='group', name=name, description=description, owner_id=current_user_id, is_public=False, invite_link=invite_link, created_at=datetime.utcnow())
    db.session.add(chat)
    db.session.flush()

    db.session.add(ChatMember(user_id=current_user_id, chat_id=chat.id, role='owner'))
    for mid in member_ids:
        if mid != current_user_id:
            db.session.add(ChatMember(user_id=mid, chat_id=chat.id, role='member'))

    for role in ('owner', 'admin', 'member'):
        db.session.add(GroupPermission(chat_id=chat.id, role=role, can_send_messages=True, can_send_media=True,
                                        can_add_members=role != 'member', can_pin_messages=role != 'member',
                                        can_change_info=role != 'member', can_delete_messages=role != 'member', can_ban_users=role == 'owner'))
    db.session.commit()

    return jsonify({'success': True, 'data': {'group': _serialize_group(chat)}}), 201


@spav2_groups_bp.route('/send_group_message', methods=['POST'])
def send_group_message():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    data = request.get_json() or {}
    group_id = data.get('group_id')
    content = data.get('content', '').strip()
    reply_to_id = data.get('reply_to_id')

    if not group_id:
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'group_id is required'}}), 400

    membership = ChatMember.query.filter_by(user_id=current_user_id, chat_id=group_id).first()
    if not membership:
        return jsonify({'success': False, 'error': {'code': 'NOT_MEMBER', 'message': 'You are not a member of this group'}}), 403

    msg = Message(sender_id=current_user_id, chat_id=group_id, receiver_id=current_user_id, content=content, timestamp=datetime.utcnow())
    db.session.add(msg)
    db.session.flush()

    if reply_to_id:
        original = Message.query.get(reply_to_id)
        if original:
            from app.models import Reply
            db.session.add(Reply(original_message_id=reply_to_id, reply_message_id=msg.id))

    db.session.commit()
    return jsonify({'success': True, 'data': {'message': {
        'message_id': msg.id,
        'sender_id': msg.sender_id,
        'sender_username': msg.sender.username if msg.sender else None,
        'sender_avatar_url': msg.sender.avatar_url if msg.sender else None,
        'group_id': group_id,
        'content': msg.content,
        'reply_to_id': reply_to_id,
        'file_path': None,
        'file_type': None,
        'timestamp': msg.timestamp.isoformat() if msg.timestamp else None,
        'edited_at': None
    }}}), 201


@spav2_groups_bp.route('/groups/<int:group_id>/update', methods=['POST'])
def update_group(group_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    membership = ChatMember.query.filter_by(user_id=current_user_id, chat_id=group_id).first()
    if not membership or membership.role not in ('owner', 'admin'):
        return jsonify({'success': False, 'error': {'code': 'FORBIDDEN', 'message': 'Only owners and admins can update the group'}}), 403

    data = request.get_json() or {}
    chat = Chat.query.get(group_id)
    if not chat or chat.chat_type != 'group':
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Group not found'}}), 404

    if 'name' in data:
        chat.name = data['name']
    if 'description' in data:
        chat.description = data['description']
    db.session.commit()
    return jsonify({'success': True, 'data': {'group': _serialize_group(chat)}})


@spav2_groups_bp.route('/groups/<int:group_id>/members/<int:user_id>/role', methods=['POST'])
def update_member_role(group_id, user_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    membership = ChatMember.query.filter_by(user_id=current_user_id, chat_id=group_id).first()
    if not membership or membership.role != 'owner':
        return jsonify({'success': False, 'error': {'code': 'FORBIDDEN', 'message': 'Only the owner can change member roles'}}), 403

    target = ChatMember.query.filter_by(user_id=user_id, chat_id=group_id).first()
    if not target:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Member not found'}}), 404
    if target.role == 'owner':
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Cannot change the owner role'}}), 400

    data = request.get_json() or {}
    role = data.get('role')
    if role not in ('admin', 'member'):
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Role must be one of: admin, member'}}), 400

    target.role = role
    target.updated_at = datetime.utcnow()
    db.session.commit()

    user = User.query.get(user_id)
    return jsonify({'success': True, 'data': {
        'group_id': group_id, 'user_id': user_id,
        'username': user.username if user else None,
        'role': role, 'updated_at': datetime.utcnow().isoformat()
    }})


@spav2_groups_bp.route('/join_group/<invite_link>', methods=['GET'])
def join_group(invite_link):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    chat = Chat.query.filter_by(chat_type='group', invite_link=invite_link).first()
    if not chat:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Group not found'}}), 404

    existing = ChatMember.query.filter_by(user_id=current_user_id, chat_id=chat.id).first()
    if not existing:
        db.session.add(ChatMember(user_id=current_user_id, chat_id=chat.id, role='member'))
        db.session.commit()

    owner = User.query.get(chat.owner_id)
    return jsonify({'success': True, 'data': {
        'group': {
            'group_id': chat.id, 'name': chat.name, 'description': chat.description,
            'avatar_url': chat.avatar_url, 'owner_id': chat.owner_id,
            'is_public': chat.is_public, 'member_count': ChatMember.query.filter_by(chat_id=chat.id).count(),
            'my_role': 'member',
            'joined_at': datetime.utcnow().isoformat()
        }
    }})


@spav2_groups_bp.route('/leave_group/<int:group_id>', methods=['POST'])
def leave_group(group_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    membership = ChatMember.query.filter_by(user_id=current_user_id, chat_id=group_id).first()
    if not membership:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Not a member'}}), 404

    if membership.role == 'owner':
        return jsonify({'success': False, 'error': {'code': 'OWNER_CANNOT_LEAVE', 'message': 'Owner cannot leave the group. Transfer ownership or delete the group.'}}), 403

    db.session.delete(membership)
    db.session.commit()
    return jsonify({'success': True, 'data': {'message': 'Successfully left the group', 'group_id': group_id}})
