from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from functools import wraps
from datetime import datetime, timezone
from app import db
from app.models import User, Report, Message, LoginOtp, Chat, ChatMember
from app.utils.helpers import get_current_user
from app.utils.security import rate_limit

spav2_admin_bp = Blueprint('spav2_admin', __name__, url_prefix='/api/admin')

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user or not user.is_admin:
            return jsonify({'success': False, 'error': {'code': 'FORBIDDEN', 'message': 'Admin access required'}}), 403
        return f(*args, **kwargs)

    return wrapper

@spav2_admin_bp.route('/', methods=['GET'])
def admin_page():
    user = get_current_user()
    return render_template('admin.html', current_user=user)


@spav2_admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'GET':
        return redirect(url_for('spav2_admin.admin_page'))
    username = (request.form.get('username') or '').strip()
    password = request.form.get('password', '')
    user = User.query.filter_by(username=username).first()
    if user and user.is_admin and user.check_password(password):
        session['user_id'] = user.id
        session['username'] = user.username
        session.permanent = True
        return redirect(url_for('spav2_admin.admin_page'))
    current_user = get_current_user()
    return render_template('admin.html', current_user=current_user, login_error='Invalid credentials')


@spav2_admin_bp.route('/logout', methods=['GET'])
def admin_logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('spav2_admin.admin_page'))

@spav2_admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def dashboard():
    total_users = User.query.count()
    total_reports = Report.query.count()
    pending_reports = Report.query.filter_by(status='pending').count()
    users_today = User.query.filter(User.created_at >= datetime.now(timezone.utc).replace(tzinfo=None).replace(hour=0, minute=0, second=0)).count()
    return jsonify({'success': True, 'data': {
        'total_users': total_users,
        'total_reports': total_reports,
        'pending_reports': pending_reports,
        'users_today': users_today
    }})

@spav2_admin_bp.route('/reports', methods=['GET'])
@admin_required
def list_reports():
    status_filter = request.args.get('status', 'pending')
    reports = Report.query.filter_by(status=status_filter).order_by(Report.created_at.desc()).limit(50).all()

    user_ids = set()
    for r in reports:
        user_ids.add(r.reporter_id)
        if r.reported_user_id:
            user_ids.add(r.reported_user_id)
    users = {u.id: u for u in User.query.filter(User.id.in_(user_ids)).all()} if user_ids else {}

    return jsonify({'success': True, 'data': {
        'reports': [{
            'id': r.id,
            'reporter_id': r.reporter_id,
            'reporter_username': users.get(r.reporter_id, User.query.get(r.reporter_id)).username if users.get(r.reporter_id) else None,
            'reported_user_id': r.reported_user_id,
            'reported_username': users.get(r.reported_user_id, User.query.get(r.reported_user_id)).username if r.reported_user_id and users.get(r.reported_user_id) else None,
            'reported_message_id': r.reported_message_id,
            'reason': r.reason,
            'status': r.status,
            'created_at': r.created_at.isoformat() if r.created_at else None
        } for r in reports]
    }})

@spav2_admin_bp.route('/reports/<int:report_id>/resolve', methods=['POST'])
@admin_required
def resolve_report(report_id):
    report = Report.query.get(report_id)
    if not report:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Report not found'}}), 404
    report.status = 'resolved'
    db.session.commit()
    return jsonify({'success': True, 'data': {'message': 'Report marked as resolved'}})

@spav2_admin_bp.route('/reports/<int:report_id>/dismiss', methods=['POST'])
@admin_required
def dismiss_report(report_id):
    report = Report.query.get(report_id)
    if not report:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Report not found'}}), 404
    report.status = 'dismissed'
    db.session.commit()
    return jsonify({'success': True, 'data': {'message': 'Report dismissed'}})

@spav2_admin_bp.route('/reports/<int:report_id>/action', methods=['POST'])
@admin_required
def take_action(report_id):
    report = Report.query.get(report_id)
    if not report:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Report not found'}}), 404
    data = request.get_json() or {}
    action_type = data.get('action_type', '')
    user_id = data.get('user_id')

    if action_type == 'warn':
        report.status = 'actioned_warn'
    elif action_type == 'delete_message':
        if report.reported_message_id:
            msg = Message.query.get(report.reported_message_id)
            if msg:
                msg.is_deleted = True
                msg.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
        report.status = 'actioned_deleted'
    elif action_type == 'ban_user':
        if user_id:
            user = User.query.get(user_id)
            if user:
                user.is_deleted = True
                user.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
        report.status = 'actioned_banned'
    elif action_type == 'timeout':
        report.status = 'actioned_timeout'
    else:
        report.status = 'resolved'

    db.session.commit()
    return jsonify({'success': True, 'data': {'message': f'Action applied: {action_type}', 'status': report.status}})

@spav2_admin_bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify({'success': True, 'data': {
        'users': [{
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'is_admin': u.is_admin,
            'is_bot': u.is_bot,
            'is_online': u.is_online,
            'email_verified': u.email_verified,
            'created_at': u.created_at.isoformat() if u.created_at else None
        } for u in users],
        'total': len(users)
    }})

@spav2_admin_bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@admin_required
def toggle_admin(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'User not found'}}), 404
    user.is_admin = not user.is_admin
    db.session.commit()
    return jsonify({'success': True, 'data': {'is_admin': user.is_admin}})


@spav2_admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'User not found'}}), 404
    if user.id == get_current_user().id:
        return jsonify({'success': False, 'error': {'code': 'FORBIDDEN', 'message': 'Cannot delete yourself'}}), 403
    user.is_deleted = True
    user.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.session.commit()
    return jsonify({'success': True, 'data': {'message': f'User {user.username} deleted'}})


@spav2_admin_bp.route('/users/<int:user_id>/update', methods=['POST'])
@admin_required
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'User not found'}}), 404
    data = request.get_json() or {}
    if 'username' in data:
        val = data['username'].strip()
        if val and len(val) >= 3:
            existing = User.query.filter_by(username=val).first()
            if existing and existing.id != user_id:
                return jsonify({'success': False, 'error': {'code': 'CONFLICT', 'message': 'Username taken'}}), 409
            user.username = val
    if 'email' in data:
        val = data['email'].strip().lower() if data['email'] else None
        if val:
            existing = User.query.filter_by(email=val).first()
            if existing and existing.id != user_id:
                return jsonify({'success': False, 'error': {'code': 'CONFLICT', 'message': 'Email taken'}}), 409
        user.email = val
    if 'display_name' in data:
        user.display_name = data['display_name'].strip() or None
    if 'bio' in data:
        user.bio = data['bio'].strip() or None
    db.session.commit()
    return jsonify({'success': True, 'data': {'message': 'Profile updated'}})


@spav2_admin_bp.route('/users/<int:user_id>/set-password', methods=['POST'])
@admin_required
def set_user_password(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'User not found'}}), 404
    data = request.get_json() or {}
    password = data.get('password', '')
    if len(password) < 6:
        return jsonify({'success': False, 'error': {'code': 'VALIDATION', 'message': 'Password must be at least 6 characters'}}), 400
    user.set_password(password)
    db.session.commit()
    return jsonify({'success': True, 'data': {'message': 'Password updated'}})


# ── 2FA Management ──────────────────────────────────────────

@spav2_admin_bp.route('/2fa/overview', methods=['GET'])
@admin_required
def twofa_overview():
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    total = LoginOtp.query.count()
    active = LoginOtp.query.filter_by(used=False).filter(LoginOtp.expires_at > now).count()
    expired = LoginOtp.query.filter(LoginOtp.expires_at <= now).count()
    used = LoginOtp.query.filter_by(used=True).count()
    start_of_day = now.replace(hour=0, minute=0, second=0)
    sent_today = LoginOtp.query.filter(LoginOtp.created_at >= start_of_day).count()
    return jsonify({'success': True, 'data': {
        'total': total,
        'active': active,
        'expired': expired,
        'used': used,
        'sent_today': sent_today
    }})


@spav2_admin_bp.route('/2fa/otps', methods=['GET'])
@admin_required
def twofa_list_otps():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    per_page = min(per_page, 200)
    query = LoginOtp.query.order_by(LoginOtp.id.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    user_ids = {o.user_id for o in pagination.items}
    users = {u.id: u for u in User.query.filter(User.id.in_(user_ids)).all()} if user_ids else {}

    return jsonify({'success': True, 'data': {
        'otps': [{
            'id': o.id,
            'user_id': o.user_id,
            'username': users.get(o.user_id).username if users.get(o.user_id) else None,
            'code': o.code,
            'created_at': o.created_at.isoformat() if o.created_at else None,
            'expires_at': o.expires_at.isoformat() if o.expires_at else None,
            'used': o.used,
            'expired': o.expires_at < datetime.now(timezone.utc).replace(tzinfo=None) if o.expires_at else False
        } for o in pagination.items],
        'page': page,
        'total_pages': pagination.pages,
        'total': pagination.total
    }})


@spav2_admin_bp.route('/2fa/cleanup', methods=['POST'])
@admin_required
def twofa_cleanup():
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    deleted = LoginOtp.query.filter(
        (LoginOtp.expires_at <= now) | (LoginOtp.used == True)
    ).delete()
    db.session.commit()
    return jsonify({'success': True, 'data': {'deleted': deleted}})


# ── User Creation ───────────────────────────────────────────

@spav2_admin_bp.route('/users/create', methods=['POST'])
@admin_required
def create_user():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip().lower() or None
    password = data.get('password', '')
    is_admin = data.get('is_admin', False)

    if not username or len(username) < 3:
        return jsonify({'success': False, 'error': {'code': 'VALIDATION', 'message': 'Username must be at least 3 characters'}}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'error': {'code': 'CONFLICT', 'message': 'Username taken'}}), 409
    if email and User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'error': {'code': 'CONFLICT', 'message': 'Email taken'}}), 409
    if len(password) < 6:
        return jsonify({'success': False, 'error': {'code': 'VALIDATION', 'message': 'Password must be at least 6 characters'}}), 400

    user = User(username=username, email=email, is_admin=is_admin)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'success': True, 'data': {
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin,
            'created_at': user.created_at.isoformat() if user.created_at else None
        },
        'message': f'User {user.username} created'
    }})


# ── Chat Management ─────────────────────────────────────────

@spav2_admin_bp.route('/chats', methods=['GET'])
@admin_required
def list_chats():
    chat_type = request.args.get('chat_type') or None
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    per_page = min(per_page, 200)

    query = Chat.query
    if chat_type in ('personal', 'group', 'channel'):
        query = query.filter_by(chat_type=chat_type)
    query = query.order_by(Chat.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    admin = get_current_user()
    chats_data = []
    for chat in pagination.items:
        member_count = ChatMember.query.filter_by(chat_id=chat.id).count()
        msg_count = Message.query.filter_by(chat_id=chat.id).count()
        last_msg = Message.query.filter_by(chat_id=chat.id).order_by(Message.timestamp.desc()).first()

        chat_name = chat.name or ''
        if not chat_name and chat.chat_type == 'personal':
            peer_id = chat.user2_id if chat.user1_id == admin.id else chat.user1_id
            peer = User.query.get(peer_id)
            chat_name = f'{peer.username} (personal)' if peer else f'personal #{chat.id}'

        chats_data.append({
            'id': chat.id,
            'chat_type': chat.chat_type,
            'name': chat_name or f'{chat.chat_type} #{chat.id}',
            'owner_id': chat.owner_id,
            'is_public': chat.is_public,
            'created_at': chat.created_at.isoformat() if chat.created_at else None,
            'member_count': member_count,
            'message_count': msg_count,
            'last_activity': last_msg.timestamp.isoformat() if last_msg else None
        })

    return jsonify({'success': True, 'data': {
        'chats': chats_data,
        'page': page,
        'per_page': per_page,
        'total': pagination.total,
        'total_pages': pagination.pages
    }})


@spav2_admin_bp.route('/chats/<int:chat_id>', methods=['GET'])
@admin_required
def chat_detail(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    members = ChatMember.query.filter_by(chat_id=chat_id).all()
    member_ids = [m.user_id for m in members]
    member_users = User.query.filter(User.id.in_(member_ids)).all() if member_ids else []
    msg_count = Message.query.filter_by(chat_id=chat_id).count()

    chat_name = chat.name or f'{chat.chat_type} #{chat.id}'
    return jsonify({'success': True, 'data': {
        'id': chat.id,
        'chat_type': chat.chat_type,
        'name': chat_name,
        'description': chat.description,
        'owner_id': chat.owner_id,
        'is_public': chat.is_public,
        'invite_link': chat.invite_link,
        'created_at': chat.created_at.isoformat() if chat.created_at else None,
        'message_count': msg_count,
        'members': [{'user_id': m.user_id, 'role': m.role, 'joined_at': m.joined_at.isoformat() if m.joined_at else None} for m in members],
        'member_users': [{'id': u.id, 'username': u.username, 'email': u.email} for u in member_users]
    }})


@spav2_admin_bp.route('/chats/<int:chat_id>/messages', methods=['GET'])
@admin_required
def chat_messages(chat_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    per_page = min(per_page, 200)
    chat = Chat.query.get_or_404(chat_id)
    pagination = Message.query.filter_by(chat_id=chat_id).order_by(Message.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)

    sender_ids = {m.sender_id for m in pagination.items}
    senders = {u.id: u.username for u in User.query.filter(User.id.in_(sender_ids)).all()} if sender_ids else {}

    return jsonify({'success': True, 'data': {
        'chat': {'id': chat.id, 'chat_type': chat.chat_type, 'name': chat.name or f'{chat.chat_type} #{chat.id}'},
        'messages': [{
            'id': m.id,
            'sender_id': m.sender_id,
            'sender_username': senders.get(m.sender_id, f'user #{m.sender_id}'),
            'content': m.content,
            'has_attachment': m.has_attachment,
            'file_type': m.file_type,
            'timestamp': m.timestamp.isoformat() if m.timestamp else None,
            'is_deleted': m.is_deleted,
            'is_read': m.is_read
        } for m in pagination.items],
        'page': page,
        'per_page': per_page,
        'total_pages': pagination.pages,
        'total': pagination.total
    }})


@spav2_admin_bp.route('/chats/<int:chat_id>/messages/<int:message_id>/delete', methods=['POST'])
@admin_required
def admin_delete_message(chat_id, message_id):
    msg = Message.query.get_or_404(message_id)
    if msg.chat_id != chat_id:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Message not found in this chat'}}), 404
    msg.is_deleted = True
    msg.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.session.commit()
    return jsonify({'success': True, 'data': {'message': 'Message deleted'}})


@spav2_admin_bp.route('/chats/<int:chat_id>/messages/<int:message_id>/restore', methods=['POST'])
@admin_required
def admin_restore_message(chat_id, message_id):
    msg = Message.query.get_or_404(message_id)
    if msg.chat_id != chat_id:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Message not found in this chat'}}), 404
    msg.is_deleted = False
    msg.deleted_at = None
    db.session.commit()
    return jsonify({'success': True, 'data': {'message': 'Message restored'}})
 
