from flask import Blueprint, render_template, jsonify, redirect, session, request as flask_request
import requests
import os
import logging
from urllib.parse import quote
from functools import wraps

logger = logging.getLogger(__name__)

video_int_bp = Blueprint('video', __name__, url_prefix='/video')

VIDEO_HOST = os.environ.get('VIDEO_HOST', 'localhost')
VIDEO_PORT = os.environ.get('VIDEO_PORT', '5001')
VIDEO_BASE_URL = f"http://{VIDEO_HOST}:{VIDEO_PORT}"
VIDEO_EXTERNAL_URL = os.environ.get('VIDEO_EXTERNAL_URL', '')
VIDEO_TIMEOUT = 5

def get_video_public_url():
    return VIDEO_EXTERNAL_URL or VIDEO_BASE_URL

def check_video_server():
    try:
        r = requests.get(f"{VIDEO_BASE_URL}/health", timeout=VIDEO_TIMEOUT)
        return r.status_code == 200
    except Exception:
        return False

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            if flask_request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'Not authenticated', 'login_required': True}), 401
            return redirect('/auth/login')
        return f(*args, **kwargs)
    return wrapper

def video_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not check_video_server():
            if flask_request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'Video server not running'}), 503
            return render_template('video_server_down.html'), 503
        return f(*args, **kwargs)
    return wrapper

def _vs(method, path, **kwargs):
    """Proxy to video server."""
    try:
        r = requests.request(method, f"{VIDEO_BASE_URL}{path}",
                            timeout=VIDEO_TIMEOUT, **kwargs)
        return r.json() if r.status_code == 200 else (r.text, r.status_code)
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Video server not running'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@video_int_bp.route('/')
@login_required
@video_required
def index():
    rooms = _vs('GET', '/api/rooms')
    if isinstance(rooms, tuple): rooms = {'rooms': []}
    return render_template('video_integration.html',
                         username=session.get('username'),
                         user_id=session.get('user_id'),
                         rooms=rooms,
                         video_external_url=get_video_public_url())

@video_int_bp.route('/create-room', methods=['POST'])
@login_required
@video_required
def create_room():
    body = flask_request.get_json(silent=True) or {}
    return _vs('POST', '/api/rooms', json={
        'username': session.get('username'),
        'user_id': session.get('user_id'),
        'name': body.get('room_name', f"{session.get('username')}'s Room"),
    })

@video_int_bp.route('/rooms')
@login_required
@video_required
def list_rooms():
    return _vs('GET', '/api/rooms')

@video_int_bp.route('/room/<room_id>')
@login_required
@video_required
def join_room(room_id):
    qs = f"?username={quote(session.get('username', ''))}&user_id={session.get('user_id')}"
    return redirect(f"{get_video_public_url()}/room/{room_id}{qs}")

@video_int_bp.route('/room/<room_id>/info')
@login_required
@video_required
def room_info(room_id):
    return _vs('GET', f'/api/rooms/{room_id}')

@video_int_bp.route('/health')
def health():
    ok = check_video_server()
    return jsonify({'status': 'ok' if ok else 'degraded', 'video_server': 'running' if ok else 'down',
                    'url': get_video_public_url()})

@video_int_bp.route('/leave/<room_id>', methods=['POST'])
@login_required
def leave_room(room_id):
    return jsonify({'success': True})

# ---- Call API (proxied to video server) ----
@video_int_bp.route('/call/<int:user_id>', methods=['POST'])
@login_required
@video_required
def initiate_call(user_id):
    """Ring a user. Creates a call + room on video server in ringing state."""
    return _vs('POST', '/api/calls', json={
        'caller_id': session.get('user_id'),
        'caller_username': session.get('username'),
        'callee_id': user_id,
        'callee_username': flask_request.get_json(silent=True).get('callee_username', '') if flask_request.is_json else '',
    })

@video_int_bp.route('/calls/incoming')
@login_required
def incoming_calls():
    """Poll: check for ringing calls for current user."""
    return _vs('GET', f"/api/calls/incoming?user_id={session.get('user_id')}")

@video_int_bp.route('/calls/<call_id>/accept', methods=['POST'])
@login_required
def accept_call(call_id):
    return _vs('POST', f'/api/calls/{call_id}/accept')

@video_int_bp.route('/calls/<call_id>/decline', methods=['POST'])
@login_required
def decline_call(call_id):
    return _vs('POST', f'/api/calls/{call_id}/decline')

@video_int_bp.route('/calls/<call_id>/end', methods=['POST'])
@login_required
def end_call(call_id):
    return _vs('POST', f'/api/calls/{call_id}/end')

# ---- Embed ----
@video_int_bp.route('/embed/<room_id>')
@login_required
@video_required
def embed_call(room_id):
    """Page that embeds the video room in an iframe (for main app)."""
    qs = f"?username={quote(session.get('username', ''))}&user_id={session.get('user_id')}"
    embed_url = f"{get_video_public_url()}/room/{room_id}{qs}"
    return render_template('video_embed.html',
                         embed_url=embed_url,
                         room_id=room_id,
                         username=session.get('username'))
