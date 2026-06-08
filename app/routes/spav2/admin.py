from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from functools import wraps
from datetime import datetime, timezone
from app import db
from app.models import User, Report, Message, LoginOtp
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
    page = request.args.get('page', 1, type=int)
    per_page = 20
    users = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
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
        } for u in users.items],
        'page': page,
        'total_pages': users.pages,
        'total': users.total
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
