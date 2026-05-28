from datetime import datetime
import secrets
from flask import Blueprint, request, jsonify
from app import db
from app.models import User, Call
from app.utils.helpers import get_current_user_id

spav2_calls_bp = Blueprint('spav2_calls', __name__, url_prefix='/api')


@spav2_calls_bp.route('/calls/history', methods=['GET'])
def call_history():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    calls = Call.query.filter(
        (Call.caller_id == current_user_id) | (Call.receiver_id == current_user_id)
    ).order_by(Call.started_at.desc()).limit(50).all()

    result = []
    for call in calls:
        is_outgoing = call.caller_id == current_user_id
        peer_id = call.receiver_id if is_outgoing else call.caller_id
        peer = User.query.get(peer_id)

        result.append({
            'call_id': call.id,
            'call_type': call.call_type,
            'peer': {
                'user_id': peer_id,
                'username': peer.username if peer else None,
                'avatar_url': peer.avatar_url if peer else None
            },
            'direction': 'outgoing' if is_outgoing else 'incoming',
            'status': call.status,
            'duration_seconds': call.duration_seconds or 0,
            'started_at': call.started_at.isoformat() if call.started_at else None,
            'ended_at': call.ended_at.isoformat() if call.ended_at else None
        })

    return jsonify({'success': True, 'data': {'calls': result}})


@spav2_calls_bp.route('/calls/make', methods=['POST'])
def make_call():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    data = request.get_json() or {}
    receiver_id = data.get('receiver_id')
    call_type = data.get('call_type', 'voice')

    if call_type not in ('voice', 'video'):
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Call type must be voice or video'}}), 400

    receiver = User.query.get(receiver_id)
    if not receiver:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'User not found'}}), 404

    room_token = f"room_{secrets.token_urlsafe(16)}"
    call = Call(
        call_type=call_type,
        caller_id=current_user_id,
        receiver_id=receiver_id,
        status='ringing',
        room_token=room_token,
        started_at=datetime.utcnow()
    )
    db.session.add(call)
    db.session.commit()

    return jsonify({'success': True, 'data': {'call': {
        'call_id': call.id,
        'call_type': call_type,
        'caller_id': current_user_id,
        'receiver_id': receiver_id,
        'status': 'ringing',
        'room_token': room_token,
        'started_at': call.started_at.isoformat() if call.started_at else None
    }}}), 201
