from datetime import datetime
import secrets
import os
import requests
from flask import Blueprint, request, jsonify
from app import db
from app.models import User, Call, VideoCall, VideoCallParticipant
from app.utils.helpers import get_current_user_id, get_current_user

spav2_calls_bp = Blueprint('spav2_calls', __name__, url_prefix='/api')

VIDEO_HOST = os.environ.get('VIDEO_HOST', 'localhost')
VIDEO_PORT = os.environ.get('VIDEO_PORT', '5001')
VIDEO_BASE_URL = f"http://{VIDEO_HOST}:{VIDEO_PORT}"
VIDEO_TIMEOUT = 5


@spav2_calls_bp.route('/calls/history', methods=['GET'])
def call_history():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    per_page = min(max(per_page, 1), 100)

    base_q = Call.query.filter(
        (Call.caller_id == current_user_id) | (Call.receiver_id == current_user_id)
    )
    total = base_q.count()
    pages = (total + per_page - 1) // per_page if per_page else 0

    calls = base_q.order_by(Call.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    peer_ids = set()
    for call in calls:
        peer_ids.add(call.receiver_id if call.caller_id == current_user_id else call.caller_id)
    peers = {u.id: u for u in User.query.filter(User.id.in_(peer_ids), User.is_deleted == False).all()}

    result = []
    for call in calls:
        is_outgoing = call.caller_id == current_user_id
        peer_id = call.receiver_id if is_outgoing else call.caller_id
        peer = peers.get(peer_id)

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
            'created_at': call.created_at.isoformat() if call.created_at else None,
            'ended_at': call.ended_at.isoformat() if call.ended_at else None
        })

    return jsonify({'success': True, 'data': {'calls': result, 'page': page, 'per_page': per_page, 'total': total, 'pages': pages}})


@spav2_calls_bp.route('/calls/make', methods=['POST'])
def make_call():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    data = request.get_json() or {}
    receiver_id = data.get('receiver_id')
    call_type = data.get('call_type', 'voice')

    if not isinstance(receiver_id, int):
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'receiver_id must be an integer'}}), 400

    if call_type not in ('voice', 'video'):
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Call type must be voice or video'}}), 400

    receiver = User.query.filter(User.id == receiver_id, User.is_deleted == False).first()
    if not receiver:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'User not found'}}), 404

    room_token = f"room_{secrets.token_urlsafe(16)}"
    call = Call(
        call_type=call_type,
        caller_id=current_user_id,
        receiver_id=receiver_id,
        status='ringing',
        room_token=room_token,
        created_at=datetime.utcnow()
    )
    db.session.add(call)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'DB_ERROR', 'message': 'Failed to create call'}}), 500

    return jsonify({'success': True, 'data': {'call': {
        'call_id': call.id,
        'call_type': call_type,
        'caller_id': current_user_id,
        'receiver_id': receiver_id,
        'status': 'ringing',
        'room_token': room_token,
        'created_at': call.created_at.isoformat() if call.created_at else None
    }}}), 201


@spav2_calls_bp.route('/video/create-room', methods=['POST'])
def video_create_room():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    user = get_current_user()
    data = request.get_json() or {}
    chat_id = data.get('chat_id')
    chat_type = data.get('chat_type', 'personal')

    try:
        r = requests.post(f"{VIDEO_BASE_URL}/api/rooms", json={
            'username': user.username if user else 'User',
            'user_id': current_user_id,
            'name': f"{user.username if user else 'User'}'s Video Call",
        }, timeout=VIDEO_TIMEOUT)

        if r.status_code != 200:
            return jsonify({'success': False, 'error': {'code': 'VIDEO_SERVER_ERROR', 'message': 'Video server error'}}), 502

        room_data = r.json()
        room_id = room_data.get('room_id')
        join_url = room_data.get('join_url', f"{VIDEO_BASE_URL}/room/{room_id}")

        vc = VideoCall(
            room_id=room_id,
            creator_id=current_user_id,
            call_type='video',
            status='active',
            created_at=datetime.utcnow()
        )
        db.session.add(vc)
        db.session.flush()

        participant = VideoCallParticipant(
            call_id=vc.id,
            user_id=current_user_id,
            joined_at=datetime.utcnow()
        )
        db.session.add(participant)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({'success': False, 'error': {'code': 'DB_ERROR', 'message': 'Failed to create video call'}}), 500

        return jsonify({'success': True, 'data': {
            'room_id': room_id,
            'room_url': join_url,
            'video_call_id': vc.id
        }})

    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': {'code': 'VIDEO_SERVER_OFFLINE', 'message': 'Video server not running'}}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500
