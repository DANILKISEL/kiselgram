import os
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from app import db
from app.models import User, Story, StoryView, StoryLike, StoryReaction, Message, Chat
from app.utils.helpers import get_current_user_id

spav2_stories_bp = Blueprint('spav2_stories', __name__, url_prefix='/api')

ALLOWED_IMAGE_EXTS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'heic', 'heif'}
ALLOWED_VIDEO_EXTS = {'mp4', 'webm', 'avi', 'mov', 'mkv', 'flv', 'wmv', 'm4v'}


def _story_to_dict(story, current_user_id):
    liked = StoryLike.query.filter_by(story_id=story.id, user_id=current_user_id).first() is not None
    viewed = StoryView.query.filter_by(story_id=story.id, viewer_id=current_user_id).first() is not None
    my_reaction = StoryReaction.query.filter_by(story_id=story.id, user_id=current_user_id).first()
    return {
        'story_id': story.id,
        'media_path': f"/uploads/{story.media_path}" if story.media_path else None,
        'media_type': story.media_type,
        'caption': story.caption,
        'created_at': story.created_at.isoformat() if story.created_at else None,
        'expires_at': (story.created_at + timedelta(hours=24)).isoformat() if story.created_at else None,
        'is_viewed': viewed,
        'view_count': StoryView.query.filter_by(story_id=story.id).count(),
        'like_count': StoryLike.query.filter_by(story_id=story.id).count(),
        'my_reaction': my_reaction.reaction if my_reaction else None
    }


@spav2_stories_bp.route('/stories', methods=['GET'])
def get_stories():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    cutoff = datetime.utcnow() - timedelta(hours=24)
    visible_ids = set([current_user_id])
    for (uid,) in db.session.query(Message.receiver_id).filter_by(sender_id=current_user_id).distinct():
        visible_ids.add(uid)
    for (uid,) in db.session.query(Message.sender_id).filter_by(receiver_id=current_user_id).distinct():
        visible_ids.add(uid)

    stories = Story.query.filter(Story.created_at >= cutoff, Story.user_id.in_(visible_ids)).order_by(Story.created_at.desc()).all()

    user_map = {}
    for story in stories:
        uid = story.user_id
        if uid not in user_map:
            user = story.user
            user_map[uid] = {
                'user_id': uid,
                'username': user.username,
                'avatar_url': user.avatar_url,
                'stories': [],
                'has_unviewed': False
            }
        data = _story_to_dict(story, current_user_id)
        user_map[uid]['stories'].append(data)
        if not data['is_viewed'] and uid != current_user_id:
            user_map[uid]['has_unviewed'] = True

    result = sorted(user_map.values(), key=lambda x: (
        0 if x['user_id'] == current_user_id else 1,
        0 if x['has_unviewed'] else 1,
        max(s['created_at'] or '' for s in x['stories']) if x['stories'] else ''
    ))

    return jsonify({'success': True, 'data': {'stories': result}})


@spav2_stories_bp.route('/stories/create', methods=['POST'])
def create_story():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    if 'media' not in request.files:
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Media file is required'}}), 400

    file = request.files['media']
    if file.filename == '':
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'No file selected'}}), 400

    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext in ALLOWED_IMAGE_EXTS:
        media_type = 'image'
    elif ext in ALLOWED_VIDEO_EXTS:
        media_type = 'video'
    else:
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Unsupported media type'}}), 400

    filename = f"story_{current_user_id}_{secrets.token_urlsafe(8)}.{ext}"
    rel_path = os.path.join('stories', filename)
    abs_dir = os.path.join('uploads', 'stories')
    os.makedirs(abs_dir, exist_ok=True)
    file.save(os.path.join(abs_dir, filename))

    caption = request.form.get('caption', '')
    privacy = request.form.get('privacy', 'everyone')

    story = Story(user_id=current_user_id, media_path=rel_path, media_type=media_type, caption=caption, created_at=datetime.utcnow())
    if hasattr(story, 'privacy_type'):
        story.privacy_type = privacy
    db.session.add(story)
    db.session.commit()

    return jsonify({'success': True, 'data': {'story': _story_to_dict(story, current_user_id)}}), 201


@spav2_stories_bp.route('/stories/<int:story_id>/view', methods=['POST'])
def view_story(story_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    story = Story.query.get_or_404(story_id)
    existing = StoryView.query.filter_by(story_id=story_id, viewer_id=current_user_id).first()
    if not existing:
        db.session.add(StoryView(story_id=story_id, viewer_id=current_user_id, viewed_at=datetime.utcnow()))
        db.session.commit()
        viewed_at = datetime.utcnow().isoformat()
    else:
        viewed_at = existing.viewed_at.isoformat() if existing.viewed_at else datetime.utcnow().isoformat()

    return jsonify({'success': True, 'data': {'story_id': story_id, 'viewed': True, 'viewed_at': viewed_at}})


@spav2_stories_bp.route('/stories/<int:story_id>/like', methods=['POST'])
def like_story(story_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    existing = StoryLike.query.filter_by(story_id=story_id, user_id=current_user_id).first()
    if existing:
        db.session.delete(existing)
        liked = False
    else:
        db.session.add(StoryLike(story_id=story_id, user_id=current_user_id))
        liked = True
    db.session.commit()

    count = StoryLike.query.filter_by(story_id=story_id).count()
    return jsonify({'success': True, 'data': {'story_id': story_id, 'liked': liked, 'like_count': count}})


@spav2_stories_bp.route('/stories/<int:story_id>/reaction', methods=['POST'])
def react_to_story(story_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    data = request.get_json() or {}
    reaction = data.get('reaction', '').strip()

    valid_reactions = ['heart', 'fire', 'laugh', 'wow', 'sad', 'angry']
    if reaction not in valid_reactions:
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': f'Reaction must be one of: {", ".join(valid_reactions)}'}}), 400

    existing = StoryReaction.query.filter_by(story_id=story_id, user_id=current_user_id).first()
    if existing:
        existing.reaction = reaction
    else:
        db.session.add(StoryReaction(story_id=story_id, user_id=current_user_id, reaction=reaction))
    db.session.commit()

    count = StoryReaction.query.filter_by(story_id=story_id).count()
    return jsonify({'success': True, 'data': {'story_id': story_id, 'reaction': reaction, 'reaction_count': count}})


@spav2_stories_bp.route('/stories/<int:story_id>/reply', methods=['POST'])
def reply_to_story(story_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    data = request.get_json() or {}
    reply_text = data.get('reply_text', '').strip()
    if not reply_text:
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'reply_text is required'}}), 400

    story = Story.query.get_or_404(story_id)
    a, b = sorted([current_user_id, story.user_id])
    chat = Chat.query.filter_by(chat_type='personal', user1_id=a, user2_id=b).first()
    if not chat:
        chat = Chat(chat_type='personal', user1_id=a, user2_id=b)
        db.session.add(chat)
        db.session.flush()

    msg = Message(content=reply_text, sender_id=current_user_id, receiver_id=story.user_id, chat_id=chat.id, timestamp=datetime.utcnow())
    db.session.add(msg)
    db.session.commit()

    return jsonify({'success': True, 'data': {'message': {
        'message_id': msg.id, 'sender_id': msg.sender_id,
        'receiver_id': msg.receiver_id, 'content': msg.content,
        'reply_to_story_id': story_id,
        'timestamp': msg.timestamp.isoformat() if msg.timestamp else None
    }}})


@spav2_stories_bp.route('/stories/<int:story_id>/stats', methods=['GET'])
def story_stats(story_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    story = Story.query.get_or_404(story_id)
    if story.user_id != current_user_id:
        return jsonify({'success': False, 'error': {'code': 'FORBIDDEN', 'message': 'Not authorized'}}), 403

    views_q = StoryView.query.filter_by(story_id=story_id).order_by(StoryView.viewed_at.desc()).all()
    likes_q = StoryLike.query.filter_by(story_id=story_id).order_by(StoryLike.created_at.desc()).all()
    reactions_q = StoryReaction.query.filter_by(story_id=story_id).order_by(StoryReaction.created_at.desc()).all()

    return jsonify({'success': True, 'data': {
        'story_id': story_id,
        'views': {
            'count': len(views_q),
            'users': [{
                'user_id': v.viewer_id,
                'username': User.query.get(v.viewer_id).username if User.query.get(v.viewer_id) else None,
                'viewed_at': v.viewed_at.isoformat() if v.viewed_at else None
            } for v in views_q]
        },
        'likes': {
            'count': len(likes_q),
            'users': [{
                'user_id': l.user_id,
                'username': User.query.get(l.user_id).username if User.query.get(l.user_id) else None
            } for l in likes_q]
        },
        'reactions': [{
            'reaction': r.reaction,
            'count': StoryReaction.query.filter_by(story_id=story_id, reaction=r.reaction).count(),
            'users': [u.username for u in User.query.join(StoryReaction, User.id == StoryReaction.user_id).filter(StoryReaction.story_id == story_id, StoryReaction.reaction == r.reaction).all()]
        } for r in reactions_q]
    }})


@spav2_stories_bp.route('/stories/<int:story_id>', methods=['DELETE'])
def delete_story(story_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    story = Story.query.get_or_404(story_id)
    if story.user_id != current_user_id:
        return jsonify({'success': False, 'error': {'code': 'FORBIDDEN', 'message': 'Not authorized'}}), 403

    if story.media_path:
        full = os.path.join('uploads', story.media_path)
        if os.path.exists(full):
            os.remove(full)
    db.session.delete(story)
    db.session.commit()
    return jsonify({'success': True, 'data': {'message': 'Story deleted'}})
