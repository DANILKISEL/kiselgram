import os, uuid, time, logging, threading
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates')
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', os.urandom(24).hex()),
    HOST=os.environ.get('VIDEO_HOST') or os.environ.get('HOST', '0.0.0.0'),
    PORT=int(os.environ.get('VIDEO_PORT') or os.environ.get('PORT', '5001')),
    EXTERNAL_URL=os.environ.get('VIDEO_EXTERNAL_URL', ''),
    MAX_ROOM_AGE=7200,
    TRUSTED_PROXIES=int(os.environ.get('TRUSTED_PROXIES', '1')),
    PRODUCTION=os.environ.get('VIDEO_PRODUCTION', '').lower() in ('1', 'true', 'yes'),
)
CORS(app)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=app.config['TRUSTED_PROXIES'], x_proto=1, x_host=1)
socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=60, ping_interval=25)

rooms, participants = {}, {}

_main_app = None
def _ensure_db():
    global _main_app
    if not app.config['PRODUCTION'] or _main_app: return
    import sys
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root not in sys.path: sys.path.insert(0, root)
    from app import create_app
    _main_app = create_app()
    _main_app.app_context().push()
    logger.info("Production DB connected")

def _resolve_user(user_id):
    if not app.config['PRODUCTION']: return None
    _ensure_db()
    from app.models import User
    try:
        with _main_app.app_context():
            u = User.query.get(int(user_id))
            return (u.id, u.username) if u else None
    except: return None

def _cleanup():
    while True:
        time.sleep(300); now = time.time()
        for rid in list(rooms.keys()):
            if now - rooms[rid].get('_ts', 0) > app.config['MAX_ROOM_AGE'] and not participants.get(rid):
                rooms.pop(rid, None); participants.pop(rid, None)
threading.Thread(target=_cleanup, daemon=True).start()

def _url(): return app.config['EXTERNAL_URL'] or f"http://localhost:{app.config['PORT']}"

@app.route('/')
def index():
    return jsonify({'status': 'ok', 'rooms': len(rooms), 'participants': sum(len(p) for p in participants.values())})

@app.route('/api/rooms')
def list_rooms():
    return jsonify({'success': True, 'rooms': [
        {'id': rid, 'name': r.get('name'), 'created_by': r.get('created_by'),
         'participants': len(participants.get(rid, {})), 'max_participants': r.get('max_participants', 10)}
        for rid, r in rooms.items()]})

@app.route('/api/rooms', methods=['POST'])
def create_room():
    b = request.get_json(silent=True) or {}
    rid = uuid.uuid4().hex[:8]
    rooms[rid] = {'name': b.get('name', f"{b.get('username','Anonymous')}'s Room"),
                  'created_by': b.get('username', 'Anonymous'),
                  'created_by_id': b.get('user_id', uuid.uuid4().hex),
                  'created_at': datetime.now(timezone.utc).isoformat(),
                  'max_participants': min(int(b.get('max_participants', 10)), 50),
                  'active': True, '_ts': time.time()}
    logger.info(f"Room {rid} created by {b.get('username')}")
    return jsonify({'success': True, 'room_id': rid, 'join_url': f"{_url()}/room/{rid}"})

@app.route('/api/rooms/<rid>')
def get_room(rid):
    r = rooms.get(rid)
    if not r: return jsonify({'error': 'Not found'}), 404
    pl = [{'username': u.get('username'), 'user_id': u.get('user_id'),
           'audio': u.get('audio', True), 'video': u.get('video', True)}
          for u in participants.get(rid, {}).values()]
    return jsonify({'success': True, 'room': {**r, 'participants': pl, 'participant_count': len(pl)}})

@app.route('/api/rooms/<rid>', methods=['DELETE'])
def delete_room(rid):
    r = rooms.get(rid)
    if not r: return jsonify({'error': 'Not found'}), 404
    if (request.get_json(silent=True) or {}).get('user_id') != r.get('created_by_id'):
        return jsonify({'error': 'Only creator can delete'}), 403
    socketio.emit('room-closed', {'room_id': rid}, room=f'room-{rid}')
    rooms.pop(rid, None); participants.pop(rid, None)
    return jsonify({'success': True})

@app.route('/join')
def join_page():
    return render_template('join.html')

@app.route('/room/<rid>')
def room_page(rid):
    r = rooms.get(rid)
    if not r: return render_template('room.html', error='not_found', room_id=rid, room_name='', username='')
    if len(participants.get(rid, {})) >= r.get('max_participants', 10):
        return render_template('room.html', error='room_full', room_id=rid, room_name=r['name'], username='',
                               max_participants=r['max_participants'])
    username = request.args.get('username', 'Anonymous')
    if app.config['PRODUCTION']:
        resolved = _resolve_user(request.args.get('user_id', '0'))
        if not resolved: return render_template('room.html', error='unauthorised', room_id='', room_name='', username=''), 403
        _, username = resolved
    return render_template('room.html', error='', room_id=rid, room_name=r.get('name', 'Room'), username=username)

@socketio.on('join-room')
def handle_join(data):
    rid, username, uid = data.get('room'), data.get('username', 'Anonymous'), data.get('user_id', '0')
    if app.config['PRODUCTION']:
        resolved = _resolve_user(uid)
        if not resolved: emit('error', {'message': 'Auth failed'}); return
        uid, username = resolved
    if rid not in rooms: emit('error', {'message': 'Room not found'}); return
    participants.setdefault(rid, {})
    sid = request.sid
    participants[rid][sid] = {'username': username, 'user_id': str(uid), 'audio': True, 'video': True,
                              'joined_at': datetime.now(timezone.utc).isoformat()}
    join_room(f'room-{rid}')
    emit('user-joined', {'sid': sid, 'username': username, 'user_id': str(uid), 'count': len(participants[rid])},
         room=f'room-{rid}', include_self=False)
    emit('room-info', {'room_id': rid, 'room_name': rooms[rid].get('name'), 'participants': [
        {'sid': s, 'username': u['username'], 'user_id': u['user_id'],
         'audio': u.get('audio', True), 'video': u.get('video', True)}
        for s, u in participants[rid].items() if s != sid]}, room=sid)

@socketio.on('offer')
def h_offer(d): emit('offer', {'offer': d['offer'], 'from': request.sid}, room=d['to'])
@socketio.on('answer')
def h_answer(d): emit('answer', {'answer': d['answer'], 'from': request.sid}, room=d['to'])
@socketio.on('ice-candidate')
def h_ice(d): emit('ice-candidate', {'candidate': d['candidate'], 'from': request.sid}, room=d['to'])

@socketio.on('toggle-audio')
def h_audio(d):
    if d.get('room') in participants and request.sid in participants[d['room']]:
        participants[d['room']][request.sid]['audio'] = not d.get('muted', False)
        emit('user-audio-changed', {'sid': request.sid, 'muted': d.get('muted', False)},
             room=f'room-{d["room"]}', include_self=False)

@socketio.on('toggle-video')
def h_video(d):
    if d.get('room') in participants and request.sid in participants[d['room']]:
        participants[d['room']][request.sid]['video'] = d.get('enabled', True)
        emit('user-video-changed', {'sid': request.sid, 'enabled': d.get('enabled', True)},
             room=f'room-{d["room"]}', include_self=False)

@socketio.on('chat-message')
def h_chat(d):
    if d.get('room') in rooms:
        emit('chat-message', {'username': d.get('username', 'Anonymous'), 'message': d.get('message'), 'from': request.sid},
             room=f'room-{d["room"]}', include_self=False)

@socketio.on('leave-room')
def h_leave(d): _remove_user(d.get('room'))
@socketio.on('disconnect')
def h_disconnect():
    for rid in list(participants):
        if request.sid in participants.get(rid, {}): _remove_user(rid); break

def _remove_user(rid):
    if rid not in participants or request.sid not in participants[rid]: return
    user = participants[rid].pop(request.sid)
    leave_room(f'room-{rid}')
    emit('user-left', {'sid': request.sid, 'username': user.get('username')}, room=f'room-{rid}')
    if not participants[rid]: logger.info(f"Room {rid} empty")

@app.errorhandler(404)
def nf(e): return jsonify({'error': 'Not found'}), 404

def run():
    print(f"Video server on {app.config['HOST']}:{app.config['PORT']}")
    socketio.run(app, host=app.config['HOST'], port=app.config['PORT'], debug=True, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    run()
