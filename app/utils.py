import hashlib
import secrets
import os
import uuid
import re
from PIL import Image
from datetime import datetime

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_invite_link():
    return secrets.token_urlsafe(16)

def allowed_file(filename, allowed_extensions, file_type='all'):
    """Check if file extension is allowed"""
    if '.' not in filename:
        return False

    ext = filename.rsplit('.', 1)[1].lower()

    if file_type == 'all':
        for category in allowed_extensions.values():
            if ext in category:
                return True
        return False
    elif file_type in allowed_extensions:
        return ext in allowed_extensions[file_type]

    return False

def get_file_type(filename, allowed_extensions):
    """Determine file type from extension"""
    ext = filename.rsplit('.', 1)[1].lower()

    if ext in allowed_extensions['images']:
        return 'image'
    elif ext in allowed_extensions['media']:
        if ext in {'mp4', 'avi', 'mov', 'mkv'}:
            return 'video'
        return 'audio'
    elif ext in allowed_extensions['documents']:
        return 'document'
    elif ext in allowed_extensions['archives']:
        return 'archive'
    else:
        return 'unknown'

def create_thumbnail(image_path, thumbnail_path, size=(200, 200)):
    """Create thumbnail for images"""
    try:
        with Image.open(image_path) as img:
            img.thumbnail(size)
            img.save(thumbnail_path, 'JPEG' if thumbnail_path.lower().endswith('.jpg') else 'PNG')
        return True
    except Exception as e:
        print(f"Thumbnail creation failed: {e}")
        return False

def format_file_size(size_bytes):
    """Convert bytes to human readable format"""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"

def setup_bots(db, User, TelegramBot, hash_password, secrets):
    """Initialize bot users"""
    bots_data = [
        {'name': 'Weather Bot', 'username': 'weather_bot', 'description': 'Get weather information'},
        {'name': 'News Bot', 'username': 'news_bot', 'description': 'Latest news headlines'},
        {'name': 'Calculator Bot', 'username': 'calc_bot', 'description': 'Mathematical calculations'},
        {'name': 'Kiselgram Help', 'username': 'kiselgram_bot', 'description': 'Official help'}
    ]

    for bot_data in bots_data:
        if not User.query.filter_by(username=bot_data['username']).first():
            bot_user = User(username=bot_data['username'], password_hash=hash_password(secrets.token_hex(16)) if bot_data['username'] != "kiselgram_bot" else "kiselgramsupport")
            db.session.add(bot_user)
        if not TelegramBot.query.filter_by(username=bot_data['username']).first():
            telegram_bot = TelegramBot(**bot_data)
            db.session.add(telegram_bot)

    db.session.commit()
