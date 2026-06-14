from flask import Blueprint, request, jsonify
from app import db
from app.models import User, Referral
from app.utils.helpers import get_current_user_id
from app.utils.security import check_user_access

spav2_referrals_bp = Blueprint('spav2_referrals', __name__, url_prefix='/api')


@spav2_referrals_bp.route('/referrals/info', methods=['GET'])
def referral_info():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'User not found'}}), 404

    count = Referral.query.filter_by(inviter_id=current_user_id).count()
    threshold = 10
    invite_url = f"https://kiselgram.ru/join?ref={user.username}"

    return jsonify({'success': True, 'data': {
        'invite_code': user.username,
        'invite_url': invite_url,
        'count': count,
        'threshold': threshold,
        'has_premium': user.is_premium,
    }})


@spav2_referrals_bp.route('/referrals/use', methods=['POST'])
def use_referral():
    data = request.get_json() or {}
    code = data.get('ref', '').strip()
    user_id = data.get('user_id')

    if not code or not user_id:
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'ref and user_id required'}}), 400

    inviter = User.query.filter_by(username=code).first()
    if not inviter:
        return jsonify({'success': False, 'error': {'code': 'INVALID_CODE', 'message': 'Invalid referral code'}}), 404

    if inviter.id == user_id:
        return jsonify({'success': False, 'error': {'code': 'SELF_REFERRAL', 'message': 'Cannot refer yourself'}}), 400

    existing = Referral.query.filter_by(invited_user_id=user_id).first()
    if existing:
        return jsonify({'success': True, 'data': {'already_applied': True}})

    ref = Referral(inviter_id=inviter.id, invited_user_id=user_id)
    db.session.add(ref)
    db.session.flush()

    count = Referral.query.filter_by(inviter_id=inviter.id).count()
    if count >= 10 and not inviter.is_premium:
        inviter.is_premium = True

    db.session.commit()

    return jsonify({'success': True, 'data': {
        'inviter_username': inviter.username,
        'count': count,
        'premium_granted': count >= 10,
    }})


@spav2_referrals_bp.route('/referrals/list', methods=['GET'])
def referral_list():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    refs = Referral.query.filter_by(inviter_id=current_user_id).order_by(Referral.created_at.desc()).all()
    users = User.query.filter(User.id.in_([r.invited_user_id for r in refs])).all()
    user_map = {u.id: u for u in users}

    return jsonify({'success': True, 'data': [{
        'username': user_map[r.invited_user_id].username if r.invited_user_id in user_map else 'deleted',
        'created_at': r.created_at.isoformat(),
    } for r in refs]})
