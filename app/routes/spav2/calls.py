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
            started_at=datetime.utcnow()
        )
        db.session.add(vc)
        db.session.flush()

        participant = VideoCallParticipant(
            call_id=vc.id,
            user_id=current_user_id,
            joined_at=datetime.utcnow()
        )
        db.session.add(participant)
        db.session.commit()

        return jsonify({'success': True, 'data': {
            'room_id': room_id,
            'room_url': join_url,
            'video_call_id': vc.id
        }})

    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': {'code': 'VIDEO_SERVER_OFFLINE', 'message': 'Video server not running'}}), 503
    except Exception as e:
        return jsonify({'success': False, 'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500
