from datetime import datetime
from flask import Blueprint, request, jsonify
from app import db
from app.models import UserMusic, Message, File
from app.utils.helpers import get_current_user_id

spav2_music_bp = Blueprint('spav2_music', __name__, url_prefix='/api')


@spav2_music_bp.route('/music/library', methods=['GET'])
def list_music():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    tracks = UserMusic.query.filter_by(user_id=current_user_id).order_by(UserMusic.added_at.desc()).limit(100).all()

    return jsonify({'success': True, 'data': {
        'tracks': [{
            'id': t.id,
            'file_url': t.file_url,
            'file_name': t.file_name,
            'artist': t.artist,
            'title': t.title,
            'duration': t.duration,
            'source_message_id': t.source_message_id,
            'added_at': t.added_at.isoformat() if t.added_at else None
        } for t in tracks]
    }})


@spav2_music_bp.route('/music/library', methods=['POST'])
def add_music():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    data = request.get_json() or {}
    file_url = data.get('file_url')
    if not file_url:
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'file_url required'}}), 400

    existing = UserMusic.query.filter_by(user_id=current_user_id, file_url=file_url).first()
    if existing:
        return jsonify({'success': False, 'error': {'code': 'ALREADY_EXISTS', 'message': 'Already in your library'}}), 400

    track = UserMusic(
        user_id=current_user_id,
        file_url=file_url,
        file_name=data.get('file_name'),
        artist=data.get('artist'),
        title=data.get('title'),
        duration=data.get('duration', 0),
        source_message_id=data.get('source_message_id'),
        added_at=datetime.utcnow()
    )
    db.session.add(track)
    db.session.commit()

    return jsonify({'success': True, 'data': {
        'id': track.id,
        'file_url': track.file_url,
        'file_name': track.file_name,
        'artist': track.artist,
        'title': track.title,
        'duration': track.duration,
        'added_at': track.added_at.isoformat() if track.added_at else None
    }}), 201


@spav2_music_bp.route('/music/library/<int:track_id>', methods=['DELETE'])
def remove_music(track_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    track = UserMusic.query.filter_by(id=track_id, user_id=current_user_id).first()
    if not track:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Track not found'}}), 404

    db.session.delete(track)
    db.session.commit()

    return jsonify({'success': True, 'data': {'id': track_id}})
