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

@video_int_bp.route('/')
@login_required
@video_required
def index():
    try:
        r = requests.get(f"{VIDEO_BASE_URL}/api/rooms", timeout=VIDEO_TIMEOUT)
        rooms = r.json() if r.status_code == 200 else {'rooms': []}
    except Exception:
        rooms = {'rooms': []}
    return render_template('video_integration.html',
                         username=session.get('username'),
                         user_id=session.get('user_id'),
                         rooms=rooms,
                         video_external_url=get_video_public_url())

@video_int_bp.route('/create-room', methods=['POST'])
@login_required
@video_required
def create_room():
    try:
        body = flask_request.get_json(silent=True) or {}
        r = requests.post(f"{VIDEO_BASE_URL}/api/rooms", json={
            'username': session.get('username'),
            'user_id': session.get('user_id'),
            'name': body.get('room_name', f"{session.get('username')}'s Room"),
        }, timeout=VIDEO_TIMEOUT)
        return r.json() if r.status_code == 200 else (r.text, r.status_code)
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Video server not running'}), 503
    except Exception as e:
        logger.error(f"create_room error: {e}")
        return jsonify({'error': str(e)}), 500

@video_int_bp.route('/rooms')
@login_required
@video_required
def list_rooms():
    try:
        r = requests.get(f"{VIDEO_BASE_URL}/api/rooms", timeout=VIDEO_TIMEOUT)
        return jsonify(r.json()) if r.status_code == 200 else (r.text, r.status_code)
    except Exception:
        return jsonify({'error': 'Video server not running'}), 503

@video_int_bp.route('/room/<room_id>')
@login_required
@video_required
def join_room(room_id):
    qs = f"?username={quote(session.get('username', ''))}&user_id={session.get('user_id')}"
    public_url = get_video_public_url()
    return redirect(f"{public_url}/room/{room_id}{qs}")

@video_int_bp.route('/room/<room_id>/info')
@login_required
@video_required
def room_info(room_id):
    try:
        r = requests.get(f"{VIDEO_BASE_URL}/api/rooms/{room_id}", timeout=VIDEO_TIMEOUT)
        return jsonify(r.json()) if r.status_code == 200 else (r.text, r.status_code)
    except Exception:
        return jsonify({'error': 'Video server not running'}), 503

@video_int_bp.route('/health')
def health():
    if check_video_server():
        return jsonify({'status': 'ok', 'video_server': 'running', 'url': get_video_public_url()})
    return jsonify({'status': 'degraded', 'video_server': 'down', 'url': get_video_public_url()}), 503

@video_int_bp.route('/leave/<room_id>', methods=['POST'])
@login_required
def leave_room(room_id):
    return jsonify({'success': True})
