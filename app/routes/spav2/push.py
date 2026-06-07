from flask import Blueprint, request, jsonify
from app import db
from app.models import PushSubscription
from app.utils.helpers import get_current_user

spav2_push_bp = Blueprint('spav2_push', __name__, url_prefix='/api/push')

@spav2_push_bp.route('/subscribe', methods=['POST'])
def subscribe():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401
    data = request.get_json() or {}
    endpoint = data.get('endpoint')
    p256dh = data.get('keys', {}).get('p256dh') if isinstance(data.get('keys'), dict) else data.get('p256dh')
    auth = data.get('keys', {}).get('auth') if isinstance(data.get('keys'), dict) else data.get('auth')
    if not endpoint or not p256dh or not auth:
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'endpoint, p256dh, and auth required'}}), 400
    existing = PushSubscription.query.filter_by(endpoint=endpoint).first()
    if existing:
        existing.user_id = user.id
        existing.p256dh = p256dh
        existing.auth = auth
    else:
        sub = PushSubscription(user_id=user.id, endpoint=endpoint, p256dh=p256dh, auth=auth)
        db.session.add(sub)
    db.session.commit()
    return jsonify({'success': True, 'data': {'message': 'Subscribed'}})

@spav2_push_bp.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401
    data = request.get_json() or {}
    endpoint = data.get('endpoint')
    if endpoint:
        PushSubscription.query.filter_by(endpoint=endpoint).delete()
    else:
        PushSubscription.query.filter_by(user_id=user.id).delete()
    db.session.commit()
    return jsonify({'success': True, 'data': {'message': 'Unsubscribed'}})

@spav2_push_bp.route('/vapid-public-key', methods=['GET'])
def vapid_public_key():
    from flask import current_app
    key = current_app.config.get('VAPID_PUBLIC_KEY', '')
    return jsonify({'success': True, 'data': {'public_key': key}})
