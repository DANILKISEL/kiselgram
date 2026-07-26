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


def _require_premium(user_id):
    user = User.query.get(user_id)
    if not user or not (user.premium and user.premium.is_premium):
        return jsonify({'success': False, 'error': {'code': 'PREMIUM_REQUIRED', 'message': 'Premium feature. Upgrade to access stories.'}}), 403
    return None


def _story_to_dict(story, current_user_id, liked=False, viewed=False, my_reaction=None, view_count=0, like_count=0):
    return {
        'story_id': story.id,
        'media_path': f"/uploads/{story.media_path}" if story.media_path else None,
        'media_type': story.media_type,
        'caption': story.caption,
        'created_at': story.created_at.isoformat() if story.created_at else None,
        'expires_at': (story.created_at + timedelta(hours=24)).isoformat() if story.created_at else None,
        'is_viewed': viewed,
        'view_count': view_count,
        'like_count': like_count,
        'my_reaction': my_reaction or None
    }


@spav2_stories_bp.route('/stories', methods=['GET'])
def get_stories():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    cutoff = datetime.utcnow() - timedelta(hours=24)
    visible_ids = {current_user_id}
    for (uid,) in db.session.query(Message.receiver_id).filter_by(sender_id=current_user_id).distinct().limit(500):
        visible_ids.add(uid)
    for (uid,) in db.session.query(Message.sender_id).filter_by(receiver_id=current_user_id).distinct().limit(500):
        visible_ids.add(uid)

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    per_page = min(max(per_page, 1), 100)

    stories = Story.query.options(db.joinedload(Story.user)).filter(
        Story.created_at >= cutoff, Story.user_id.in_(visible_ids)
    ).order_by(Story.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    story_ids = [s.id for s in stories]
    my_likes = {s_id for s_id, in db.session.query(StoryLike.story_id).filter(StoryLike.story_id.in_(story_ids), StoryLike.user_id == current_user_id).all()} if story_ids else set()
    my_views = {s_id for s_id, in db.session.query(StoryView.story_id).filter(StoryView.story_id.in_(story_ids), StoryView.viewer_id == current_user_id).all()} if story_ids else set()
    my_reactions = dict(db.session.query(StoryReaction.story_id, StoryReaction.reaction).filter(StoryReaction.story_id.in_(story_ids), StoryReaction.user_id == current_user_id).all()) if story_ids else {}
    view_counts = dict(db.session.query(StoryView.story_id, db.func.count(StoryView.id)).filter(StoryView.story_id.in_(story_ids)).group_by(StoryView.story_id).all()) if story_ids else {}
    like_counts = dict(db.session.query(StoryLike.story_id, db.func.count(StoryLike.id)).filter(StoryLike.story_id.in_(story_ids)).group_by(StoryLike.story_id).all()) if story_ids else {}

    user_map = {}
    for story in stories:
        uid = story.user_id
        if uid not in user_map:
            user = story.user
            if not user or user.is_deleted:
                continue
            user_map[uid] = {
                'user_id': uid,
                'username': user.username,
                'avatar_url': user.avatar_url,
                'stories': [],
                'has_unviewed': False
            }
        data = _story_to_dict(
            story, current_user_id,
            liked=story.id in my_likes,
            viewed=story.id in my_views,
            my_reaction=my_reactions.get(story.id),
            view_count=view_counts.get(story.id, 0),
            like_count=like_counts.get(story.id, 0)
        )
        user_map[uid]['stories'].append(data)
        if not data['is_viewed'] and uid != current_user_id:
            user_map[uid]['has_unviewed'] = True

    result = sorted(user_map.values(), key=lambda x: (
        0 if x['user_id'] == current_user_id else 1,
        0 if x['has_unviewed'] else 1,
        max(s['created_at'] or '' for s in x['stories']) if x['stories'] else ''
    ))

    total = Story.query.filter(Story.created_at >= cutoff, Story.user_id.in_(visible_ids)).count()
    pages = (total + per_page - 1) // per_page if per_page else 0
    return jsonify({'success': True, 'data': {'stories': result, 'page': page, 'per_page': per_page, 'total': total, 'pages': pages}})


@spav2_stories_bp.route('/stories/create', methods=['POST'])
def create_story():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    err = _require_premium(current_user_id)
    if err:
        return err

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

    if len(caption) > 500:
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Caption too long (max 500 characters)'}}), 400
    if privacy not in ('everyone', 'contacts', 'close_friends'):
        return jsonify({'success': False, 'error': {'code': 'VALIDATION_ERROR', 'message': 'Privacy must be one of: everyone, contacts, close_friends'}}), 400

    story = Story(user_id=current_user_id, media_path=rel_path, media_type=media_type, caption=caption, created_at=datetime.utcnow())
    if hasattr(story, 'privacy_type'):
        story.privacy_type = privacy
    db.session.add(story)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'DB_ERROR', 'message': 'Failed to save story'}}), 500

    return jsonify({'success': True, 'data': {'story': _story_to_dict(story, current_user_id)}}), 201


@spav2_stories_bp.route('/stories/<int:story_id>/view', methods=['POST'])
def view_story(story_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    story = Story.query.get(story_id)
    if not story:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Story not found'}}), 404
    existing = StoryView.query.filter_by(story_id=story_id, viewer_id=current_user_id).first()
    if not existing:
        db.session.add(StoryView(story_id=story_id, viewer_id=current_user_id, viewed_at=datetime.utcnow()))
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({'success': False, 'error': {'code': 'DB_ERROR', 'message': 'Failed to record view'}}), 500
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
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'DB_ERROR', 'message': 'Failed to update like'}}), 500

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
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'DB_ERROR', 'message': 'Failed to save reaction'}}), 500

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

    story = Story.query.get(story_id)
    if not story:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Story not found'}}), 404
    a, b = sorted([current_user_id, story.user_id])
    chat = Chat.query.filter_by(chat_type='personal', user1_id=a, user2_id=b).first()
    if not chat:
        chat = Chat(chat_type='personal', user1_id=a, user2_id=b)
        db.session.add(chat)
        db.session.flush()

    msg = Message(content=reply_text, sender_id=current_user_id, receiver_id=story.user_id, chat_id=chat.id, timestamp=datetime.utcnow())
    db.session.add(msg)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'DB_ERROR', 'message': 'Failed to send reply'}}), 500

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

    story = Story.query.get(story_id)
    if not story:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Story not found'}}), 404
    if story.user_id != current_user_id:
        return jsonify({'success': False, 'error': {'code': 'FORBIDDEN', 'message': 'Not authorized'}}), 403

    views_q = StoryView.query.filter_by(story_id=story_id).order_by(StoryView.viewed_at.desc()).limit(200).all()
    likes_q = StoryLike.query.filter_by(story_id=story_id).order_by(StoryLike.created_at.desc()).limit(200).all()
    reactions_q = StoryReaction.query.filter_by(story_id=story_id).order_by(StoryReaction.created_at.desc()).limit(200).all()

    all_user_ids = set()
    for v in views_q:
        all_user_ids.add(v.viewer_id)
    for l in likes_q:
        all_user_ids.add(l.user_id)
    for r in reactions_q:
        all_user_ids.add(r.user_id)
    users_map = {u.id: u for u in User.query.filter(User.id.in_(all_user_ids), User.is_deleted == False).all()} if all_user_ids else {}

    # Group reactions by type from already-loaded data
    reaction_groups = {}
    for r in reactions_q:
        if r.reaction not in reaction_groups:
            reaction_groups[r.reaction] = {'count': 0, 'user_ids': set()}
        reaction_groups[r.reaction]['count'] += 1
        reaction_groups[r.reaction]['user_ids'].add(r.user_id)

    reactions_data = [{
        'reaction': reaction,
        'count': data['count'],
        'users': sorted(users_map[uid].username for uid in data['user_ids'] if uid in users_map)
    } for reaction, data in reaction_groups.items()]

    return jsonify({'success': True, 'data': {
        'story_id': story_id,
        'views': {
            'count': len(views_q),
            'users': [{
                'user_id': v.viewer_id,
                'username': users_map[v.viewer_id].username if v.viewer_id in users_map else None,
                'viewed_at': v.viewed_at.isoformat() if v.viewed_at else None
            } for v in views_q]
        },
        'likes': {
            'count': len(likes_q),
            'users': [{
                'user_id': l.user_id,
                'username': users_map[l.user_id].username if l.user_id in users_map else None
            } for l in likes_q]
        },
        'reactions': reactions_data
    }})


@spav2_stories_bp.route('/stories/<int:story_id>', methods=['DELETE'])
def delete_story(story_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Not authenticated'}}), 401

    story = Story.query.get(story_id)
    if not story:
        return jsonify({'success': False, 'error': {'code': 'NOT_FOUND', 'message': 'Story not found'}}), 404
    if story.user_id != current_user_id:
        return jsonify({'success': False, 'error': {'code': 'FORBIDDEN', 'message': 'Not authorized'}}), 403

    if story.media_path:
        full = os.path.join('uploads', story.media_path)
        if os.path.exists(full):
            os.remove(full)
    db.session.delete(story)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'error': {'code': 'DB_ERROR', 'message': 'Failed to delete story'}}), 500
    return jsonify({'success': True, 'data': {'message': 'Story deleted'}})
