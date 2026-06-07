from flask import Blueprint, request, jsonify, render_template, session
from functools import wraps
from datetime import datetime, timezone
from app import db
from app.models import User, Report, Message
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
@admin_required
def admin_page():
    return render_template('admin.html')

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
