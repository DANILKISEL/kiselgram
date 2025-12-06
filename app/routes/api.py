from flask import Blueprint, request, jsonify
from datetime import datetime
from app import db
from app.models import Message, GroupMember, ChannelSubscriber, User, Group, Channel
from app.utils import get_current_user, get_current_user_id, format_file_size

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/messages/<int:user_id>')
def api_messages(user_id):
    if not get_current_user():
        return jsonify({'error': 'Not authenticated'}), 401

    current_user_id = get_current_user_id()
    after_id = request.args.get('after', 0, type=int)

    messages = Message.query.filter(
        ((Message.sender_id == current_user_id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user_id))
    ).filter(Message.id > after_id).order_by(Message.timestamp.asc()).all()

    messages_data = []
    for message in messages:
        message_data = {
            'id': message.id,
            'content': message.content,
            'sender_name': message.sender.username,
            'timestamp': message.timestamp.strftime('%H:%M'),
            'is_read': message.is_read,
            'is_own': message.sender_id == current_user_id,
            'has_attachment': message.has_attachment,
        }

        if message.has_attachment:
            message_data.update({
                'file_type': message.file_type,
                'file_name': message.file_name,
                'file_size': format_file_size(message.file_size),
                'file_url': f"/{message.file_path}",
                'thumbnail_url': f"/{message.thumbnail_path}" if message.thumbnail_path else None
            })

        messages_data.append(message_data)

    return jsonify({'messages': messages_data})

@api_bp.route('/api/group_messages/<int:group_id>')
def api_group_messages(group_id):
    if not get_current_user():
        return jsonify({'error': 'Not authenticated'}), 401

    membership = GroupMember.query.filter_by(user_id=get_current_user_id(), group_id=group_id).first()
    if not membership:
        return jsonify({'error': 'Not a member'}), 403

    after_id = request.args.get('after', 0, type=int)
    messages = Message.query.filter_by(group_id=group_id).filter(Message.id > after_id).order_by(
        Message.timestamp.asc()).all()

    messages_data = []
    for message in messages:
        message_data = {
            'id': message.id,
            'content': message.content,
            'sender_name': message.sender.username,
            'timestamp': message.timestamp.strftime('%H:%M'),
            'is_own': message.sender_id == get_current_user_id(),
            'has_attachment': message.has_attachment,
        }

        if message.has_attachment:
            message_data.update({
                'file_type': message.file_type,
                'file_name': message.file_name,
                'file_size': format_file_size(message.file_size),
                'file_url': f"/{message.file_path}",
                'thumbnail_url': f"/{message.thumbnail_path}" if message.thumbnail_path else None
            })

        messages_data.append(message_data)

    return jsonify({'messages': messages_data})

@api_bp.route('/api/channel_messages/<int:channel_id>')
def api_channel_messages(channel_id):
    if not get_current_user():
        return jsonify({'error': 'Not authenticated'}), 401

    subscription = ChannelSubscriber.query.filter_by(user_id=get_current_user_id(), channel_id=channel_id).first()
    if not subscription:
        return jsonify({'error': 'Not subscribed'}), 403

    after_id = request.args.get('after', 0, type=int)
    messages = Message.query.filter_by(channel_id=channel_id).filter(Message.id > after_id).order_by(
        Message.timestamp.asc()).all()

    messages_data = []
    for message in messages:
        message_data = {
            'id': message.id,
            'content': message.content,
            'sender_name': message.sender.username,
            'timestamp': message.timestamp.strftime('%H:%M'),
            'is_own': message.sender_id == get_current_user_id(),
            'has_attachment': message.has_attachment,
        }

        if message.has_attachment:
            message_data.update({
                'file_type': message.file_type,
                'file_name': message.file_name,
                'file_size': format_file_size(message.file_size),
                'file_url': f"/{message.file_path}",
                'thumbnail_url': f"/{message.thumbnail_path}" if message.thumbnail_path else None
            })

        messages_data.append(message_data)

    return jsonify({'messages': messages_data})

@api_bp.route('/api/send_message', methods=['POST'])
def api_send_message():
    if not get_current_user():
        return jsonify({'error': 'Not authenticated'}), 401

    current_user_id = get_current_user_id()
    data = request.get_json()
    receiver_id = data.get('receiver_id')
    content = data.get('content')

    if not receiver_id or (not content and not data.get('has_attachment')):
        return jsonify({'error': 'Missing parameters'}), 400

    new_message = Message(content=content, sender_id=current_user_id, receiver_id=receiver_id)
    db.session.add(new_message)
    db.session.commit()

    message_data = {
        'id': new_message.id,
        'content': new_message.content,
        'sender_name': new_message.sender.username,
        'timestamp': new_message.timestamp.strftime('%H:%M'),
        'is_own': True,
        'has_attachment': False,
    }

    return jsonify({'success': True, 'message': message_data})

@api_bp.route('/api/send_group_message', methods=['POST'])
def api_send_group_message():
    if not get_current_user():
        return jsonify({'error': 'Not authenticated'}), 401

    current_user_id = get_current_user_id()
    data = request.get_json()
    group_id = data.get('group_id')
    content = data.get('content')

    if not group_id or (not content and not data.get('has_attachment')):
        return jsonify({'error': 'Missing parameters'}), 400

    membership = GroupMember.query.filter_by(user_id=current_user_id, group_id=group_id).first()
    if not membership:
        return jsonify({'error': 'Not a member'}), 403

    new_message = Message(content=content, sender_id=current_user_id, receiver_id=current_user_id, group_id=group_id)
    db.session.add(new_message)
    db.session.commit()

    message_data = {
        'id': new_message.id,
        'content': new_message.content,
        'sender_name': new_message.sender.username,
        'timestamp': new_message.timestamp.strftime('%H:%M'),
        'is_own': True,
        'has_attachment': False,
    }

    return jsonify({'success': True, 'message': message_data})

@api_bp.route('/api/send_channel_message', methods=['POST'])
def api_send_channel_message():
    if not get_current_user():
        return jsonify({'error': 'Not authenticated'}), 401

    current_user_id = get_current_user_id()
    data = request.get_json()
    channel_id = data.get('channel_id')
    content = data.get('content')

    if not channel_id or (not content and not data.get('has_attachment')):
        return jsonify({'error': 'Missing parameters'}), 400

    channel = Channel.query.get(channel_id)
    if not channel or channel.owner_id != current_user_id:
        return jsonify({'error': 'Not authorized'}), 403

    new_message = Message(content=content, sender_id=current_user_id, receiver_id=current_user_id,
                          channel_id=channel_id)
    db.session.add(new_message)
    db.session.commit()

    message_data = {
        'id': new_message.id,
        'content': new_message.content,
        'sender_name': new_message.sender.username,
        'timestamp': new_message.timestamp.strftime('%H:%M'),
        'is_own': True,
        'has_attachment': False,
    }

    return jsonify({'success': True, 'message': message_data})

@api_bp.route('/api/chat_list')
def api_chat_list():
    if not get_current_user():
        return jsonify({'error': 'Not authenticated'}), 401

    current_user_id = get_current_user_id()
    sent_chats = db.session.query(Message.receiver_id).filter_by(sender_id=current_user_id).distinct()
    received_chats = db.session.query(Message.sender_id).filter_by(receiver_id=current_user_id).distinct()
    chat_user_ids = set([id[0] for id in sent_chats] + [id[0] for id in received_chats])

    chats_data = []
    for user_id in chat_user_ids:
        user = User.query.get(user_id)
        if user and user.id != current_user_id:
            last_message = Message.query.filter(
                ((Message.sender_id == current_user_id) & (Message.receiver_id == user_id)) |
                ((Message.sender_id == user_id) & (Message.receiver_id == current_user_id))
            ).order_by(Message.timestamp.desc()).first()

            unread_count = Message.query.filter_by(sender_id=user_id, receiver_id=current_user_id,
                                                   is_read=False).count()

            if last_message:
                time_diff = datetime.utcnow() - last_message.timestamp
                timestamp = last_message.timestamp.strftime(
                    '%H:%M') if time_diff.days == 0 else 'Yesterday' if time_diff.days == 1 else last_message.timestamp.strftime(
                    '%d.%m.%Y')
            else:
                timestamp = ''

            chats_data.append({
                'type': 'personal',
                'id': user.id,
                'name': user.username,
                'last_message': last_message.content if last_message else '',
                'unread_count': unread_count,
                'timestamp': timestamp,
            })

    return jsonify({'chats': chats_data})