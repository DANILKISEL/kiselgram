# app/models.py

from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


# ============ USER MODELS ============

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=True)
    email_verified = db.Column(db.Boolean, default=False)
    display_name = db.Column(db.String(80), nullable=True)
    password_hash = db.Column(db.String(120), nullable=True)
    telegram_chat_id = db.Column(db.String(50), unique=True, nullable=True)
    telegram_username = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bio = db.Column(db.Text, nullable=True)
    avatar_url = db.Column(db.String(500), nullable=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    is_online = db.Column(db.Boolean, default=False)

    # Premium fields moved to UserPremium model
    is_admin = db.Column(db.Boolean, default=False)

    # Avatar type
    avatar_type = "image"

    # Notification settings
    notification_sound = db.Column(db.String(50), default='default')
    per_chat_sounds = db.Column(db.JSON, default={})
    mute_all = db.Column(db.Boolean, default=False)
    do_not_disturb = db.Column(db.Boolean, default=False)

    # Bot fields
    is_bot = db.Column(db.Boolean, default=False)
    bot_owner_id = db.Column(db.Integer, nullable=True)
    bot_token = db.Column(db.String(64), nullable=True)
    bot_webapp_url = db.Column(db.String(500), nullable=True)

    # Status emoji (Premium)
    status_emoji = db.Column(db.String(10), default='')

    # Privacy settings
    privacy_last_seen = db.Column(db.String(20), default='everyone')
    privacy_photo = db.Column(db.String(20), default='everyone')
    privacy_forward = db.Column(db.String(20), default='everyone')
    privacy_calls = db.Column(db.String(20), default='everyone')
    privacy_messages = db.Column(db.String(20), default='everyone')

    # Appearance settings
    theme = db.Column(db.String(10), default='light')
    font_size = db.Column(db.Integer, default=14)
    bubble_radius = db.Column(db.Integer, default=18)
    font_family = db.Column(db.String(100), default="'Inter', sans-serif")
    my_message_color = db.Column(db.String(20), default='#667eea')
    their_message_color = db.Column(db.String(20), default='#f3f4f6')
    wallpaper = db.Column(db.String(50), default='')
    wallpaper_image = db.Column(db.String(500), nullable=True)

    # Soft delete
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Google OAuth
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    profile_pic = db.Column(db.String(200), nullable=True)

    # Relationships
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy=True)
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy=True)
    user_reactions = db.relationship('Reaction', backref='user', lazy=True)
    blocked_users = db.relationship('BlockedUser', foreign_keys='BlockedUser.user_id', backref='user', lazy=True)
    sessions = db.relationship('UserSession', backref='user', lazy=True)
    stories = db.relationship('Story', backref='user', lazy='dynamic')
    story_views = db.relationship('StoryView', backref='viewer', lazy='dynamic')
    story_likes = db.relationship('StoryLike', backref='user', lazy='dynamic')
    story_reactions = db.relationship('StoryReaction', backref='user', lazy='dynamic')

    # Premium relationship
    premium = db.relationship('UserPremium', backref='user', uselist=False, lazy=True)

    # Chat memberships (unified)
    chat_memberships = db.relationship('ChatMember', backref='user', lazy=True)
    chat_subscriptions = db.relationship('ChatSubscriber', backref='user', lazy=True)

    # Owned chats (groups/channels)
    owned_chats = db.relationship('Chat', foreign_keys='Chat.owner_id', backref='owner', lazy=True)

    # User properties
    reports_filed = db.relationship('Report', foreign_keys='Report.reporter_id', backref='reporter', lazy=True)
    reports_received = db.relationship('Report', foreign_keys='Report.reported_user_id', backref='reported_user', lazy=True)
    push_subscriptions = db.relationship('PushSubscription', backref='user', lazy=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True)
    recent_searches = db.relationship('RecentSearch', backref='user', lazy=True)
    pinned_chats = db.relationship('PinnedChat', backref='user', lazy=True)
    email_verifications = db.relationship('EmailVerification', backref='user', lazy=True)
    k_settings = db.relationship('UserKSettings', backref='user', uselist=False, lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'display_name': self.display_name or self.username,
            'bio': self.bio,
            'avatar_url': self.avatar_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'is_online': self.is_online,
            'status_emoji': self.status_emoji,
            'is_premium': self.premium.is_premium if self.premium else False
        }

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class UserPremium(db.Model):
    """Separate premium model for users"""
    __tablename__ = 'user_premium'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    is_premium = db.Column(db.Boolean, default=False)
    premium_since = db.Column(db.DateTime, nullable=True)
    premium_expires_at = db.Column(db.DateTime, nullable=True)
    premium_auto_renew = db.Column(db.Boolean, default=False)
    premium_payment_method = db.Column(db.String(50), nullable=True)
    premium_plan = db.Column(db.String(20), nullable=True)


# ============ UNIFIED CHAT MODEL ============

class Chat(db.Model):
    """Unified chat: personal, group, or channel"""
    __tablename__ = 'chats'

    id = db.Column(db.Integer, primary_key=True)
    chat_type = db.Column(db.String(20), nullable=False)  # 'personal', 'group', 'channel'
    name = db.Column(db.String(100), nullable=True)       # For group/channel; personal uses other user's name
    description = db.Column(db.Text, nullable=True)
    avatar_url = db.Column(db.String(500), nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # For group/channel; null for personal
    is_public = db.Column(db.Boolean, default=True)       # For group/channel
    invite_link = db.Column(db.String(100), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # For personal chats: the two participants are stored in ChatMember with role='participant'
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # Relationships
    members = db.relationship('ChatMember', backref='chat', lazy='dynamic', cascade='all, delete-orphan')
    subscribers = db.relationship('ChatSubscriber', backref='chat', lazy='dynamic', cascade='all, delete-orphan')
    messages = db.relationship('Message', backref='chat', lazy='dynamic')
    permissions = db.relationship('GroupPermission', backref='chat', lazy='dynamic', cascade='all, delete-orphan')
    admins = db.relationship('ChannelAdmin', backref='chat', lazy='dynamic', cascade='all, delete-orphan')

    __table_args__ = (
        db.CheckConstraint("chat_type IN ('personal', 'group', 'channel')"),
    )


class ChatMember(db.Model):
    """Members of a group chat (or participants in personal chat)"""
    __tablename__ = 'chat_members'

    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(20), default='member')  # 'owner', 'admin', 'member', 'participant'
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('chat_id', 'user_id', name='unique_chat_member'),)


class ChatSubscriber(db.Model):
    """Subscribers of a channel"""
    __tablename__ = 'chat_subscribers'

    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('chat_id', 'user_id', name='unique_chat_subscriber'),)


class GroupPermission(db.Model):
    """Role-based permissions for groups (chat_type='group')"""
    __tablename__ = 'group_permissions'

    chat_id = db.Column(db.Integer, db.ForeignKey('chats.id', ondelete='CASCADE'), primary_key=True)
    role = db.Column(db.String(20), primary_key=True)  # 'owner', 'admin', 'member'
    can_send_messages = db.Column(db.Boolean, default=True)
    can_send_media = db.Column(db.Boolean, default=True)
    can_add_members = db.Column(db.Boolean, default=False)
    can_pin_messages = db.Column(db.Boolean, default=False)
    can_change_info = db.Column(db.Boolean, default=False)
    can_delete_messages = db.Column(db.Boolean, default=False)
    can_ban_users = db.Column(db.Boolean, default=False)


class ChannelAdmin(db.Model):
    """Channel admins with specific permissions (chat_type='channel')"""
    __tablename__ = 'channel_admins'

    chat_id = db.Column(db.Integer, db.ForeignKey('chats.id', ondelete='CASCADE'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    can_post = db.Column(db.Boolean, default=True)
    can_edit = db.Column(db.Boolean, default=False)
    can_delete = db.Column(db.Boolean, default=False)
    can_add_admins = db.Column(db.Boolean, default=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)


# ============ MESSAGE MODELS ============

class Message(db.Model):
    __tablename__ = 'message'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # For personal chat, the other user
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    telegram_message_id = db.Column(db.String(50), nullable=True)
    is_from_telegram = db.Column(db.Boolean, default=False)
    delivered_at = db.Column(db.DateTime, nullable=True)
    read_at = db.Column(db.DateTime, nullable=True)
    is_saved = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # if has file, use File model: see below

    has_attachment = db.Column(db.Boolean, default=False)
    file_type = db.Column(db.String(20), nullable=True)
    file_name = db.Column(db.String(255), nullable=True)
    file_path = db.Column(db.String(500), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    thumbnail_path = db.Column(db.String(500), nullable=True)

    is_encrypted = db.Column(db.Boolean, default=False)
    encrypted_content = db.Column(db.Text)
    encryption_key_id = db.Column(db.Integer)

    # Soft delete
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_for_all = db.Column(db.Boolean, default=False)

    # Edit timestamp
    edited_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=True)
    file = db.relationship('File', backref=db.backref('messages', lazy='dynamic'), lazy=True)

    reactions = db.relationship('Reaction', backref='message', lazy=True, cascade='all, delete-orphan')
    replies_to = db.relationship('Reply', foreign_keys='Reply.original_message_id', backref='original_message', lazy=True)
    reply_to = db.relationship('Reply', foreign_keys='Reply.reply_message_id', backref='reply_message', uselist=False, lazy=True)
    forwards_from = db.relationship('Forward', foreign_keys='Forward.original_message_id', backref='original_message', lazy=True)
    forwards_to = db.relationship('Forward', foreign_keys='Forward.forwarded_message_id', backref='forwarded_message', uselist=False, lazy=True)


class File(db.Model):
    __tablename__ = 'files'
    id = db.Column(db.Integer, primary_key=True)
    file_type = db.Column(db.String(20), nullable=True)
    file_name = db.Column(db.String(255), nullable=True)
    file_path = db.Column(db.String(500), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    thumbnail_path = db.Column(db.String(500), nullable=True)
    preview_size = db.Column(db.String(10), default='medium')
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Reaction(db.Model):
    __tablename__ = 'reaction'

    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reaction_type = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('message_id', 'user_id', 'reaction_type', name='unique_user_message_reaction'),)


class Reply(db.Model):
    __tablename__ = 'reply'

    id = db.Column(db.Integer, primary_key=True)
    original_message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=False)
    reply_message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Forward(db.Model):
    __tablename__ = 'forward'

    id = db.Column(db.Integer, primary_key=True)
    original_message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=False)
    forwarded_message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=False)
    forwarded_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    original_sender_name = db.Column(db.String(80), nullable=True)


# ============ STORY MODELS ============

class Story(db.Model):
    __tablename__ = 'stories'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    media_path = db.Column(db.String(500), nullable=False)
    media_type = db.Column(db.String(20), default='image')
    caption = db.Column(db.Text)
    music_path = db.Column(db.String(500), nullable=True)
    privacy_type = db.Column(db.String(20), default='everyone')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    views = db.relationship('StoryView', backref='story', lazy='dynamic', cascade='all, delete-orphan')
    likes = db.relationship('StoryLike', backref='story', lazy='dynamic', cascade='all, delete-orphan')
    reactions = db.relationship('StoryReaction', backref='story', lazy='dynamic', cascade='all, delete-orphan')
    privacy_settings = db.relationship('StoryPrivacy', backref='story', uselist=False, cascade='all, delete-orphan')
    allowed_users = db.relationship('StoryAllowedUser', backref='story', cascade='all, delete-orphan')


class StoryView(db.Model):
    __tablename__ = 'story_views'

    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id'), nullable=False)
    viewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)


class StoryLike(db.Model):
    __tablename__ = 'story_likes'

    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('story_id', 'user_id', name='unique_story_like'),)


class StoryReaction(db.Model):
    __tablename__ = 'story_reactions'

    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reaction = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('story_id', 'user_id', name='unique_story_reaction'),)


class StoryPrivacy(db.Model):
    __tablename__ = 'story_privacy'

    story_id = db.Column(db.Integer, db.ForeignKey('stories.id', ondelete='CASCADE'), primary_key=True)
    privacy_type = db.Column(db.String(20), default='everyone')


class StoryAllowedUser(db.Model):
    __tablename__ = 'story_allowed_users'

    story_id = db.Column(db.Integer, db.ForeignKey('stories.id', ondelete='CASCADE'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)


# ============ CONTACT MODELS ============

class Contact(db.Model):
    __tablename__ = 'contacts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    custom_name = db.Column(db.String(80), nullable=True)  # Property: a contact can have a name
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'contact_id', name='unique_contact'),)


# ============ CALL MODELS ============

class Call(db.Model):
    __tablename__ = 'calls'

    id = db.Column(db.Integer, primary_key=True)
    caller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    call_type = db.Column(db.String(10), default='audio')  # 'audio' or 'video'
    status = db.Column(db.String(20), default='ringing')   # ringing, answered, ended
    duration = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class VideoCall(db.Model):
    """Persistent record of a video room session"""
    __tablename__ = 'video_calls'

    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(50), unique=True, nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    call_type = db.Column(db.String(10), default='video')
    status = db.Column(db.String(20), default='active')
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)
    duration = db.Column(db.Integer, default=0)
    participant_count = db.Column(db.Integer, default=1)


class VideoCallParticipant(db.Model):
    """Participants in a video call"""
    __tablename__ = 'video_call_participants'

    id = db.Column(db.Integer, primary_key=True)
    call_id = db.Column(db.Integer, db.ForeignKey('video_calls.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    left_at = db.Column(db.DateTime, nullable=True)
    audio_only = db.Column(db.Boolean, default=False)
    screensharing = db.Column(db.Boolean, default=False)


# ============ OTHER MODELS (USER PROPERTIES) ============

class BlockedUser(db.Model):
    __tablename__ = 'blocked_users'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    blocked_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    blocked_user = db.relationship('User', foreign_keys=[blocked_user_id], backref='blocked_by')
    __table_args__ = (db.UniqueConstraint('user_id', 'blocked_user_id', name='unique_block'),)


class UserSession(db.Model):
    __tablename__ = 'user_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_token = db.Column(db.String(255), unique=True, nullable=False)
    device = db.Column(db.String(200), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)


class Report(db.Model):
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reported_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    reported_message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=True)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reported_message = db.relationship('Message', foreign_keys=[reported_message_id])


class PushSubscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    endpoint = db.Column(db.Text, nullable=False)
    p256dh = db.Column(db.Text, nullable=False)
    auth = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Favorite(db.Model):
    __tablename__ = 'favorites'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    file_type = db.Column(db.String(20), nullable=True)
    file_path = db.Column(db.String(500), nullable=True)
    file_name = db.Column(db.String(255), nullable=True)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class RecentSearch(db.Model):
    __tablename__ = 'recent_searches'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    search_query = db.Column(db.String(200), nullable=False)
    search_type = db.Column(db.String(20), default='all')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class PreloadedAvatar(db.Model):
    __tablename__ = 'preloaded_avatars'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), unique=True, nullable=False)
    display_name = db.Column(db.String(50))
    category = db.Column(db.String(20), default='default')


class PinnedChat(db.Model):
    """Pinned chats for a user"""
    __tablename__ = 'pinned_chats'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    chat_type = db.Column(db.String(20), nullable=False)   # 'personal', 'group', 'channel'
    chat_id = db.Column(db.Integer, nullable=False)
    pinned_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'chat_type', 'chat_id', name='unique_pin'),)


class EmailVerification(db.Model):
    __tablename__ = 'email_verifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    email = db.Column(db.String(128), nullable=True, index=True)
    token = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    verified = db.Column(db.Boolean, default=False)


class UserMusic(db.Model):
    __tablename__ = 'user_music'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    file_url = db.Column(db.String(500), nullable=False)
    file_name = db.Column(db.String(255), nullable=True)
    artist = db.Column(db.String(255), nullable=True)
    title = db.Column(db.String(255), nullable=True)
    duration = db.Column(db.Integer, default=0)
    source_message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=True)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)


class UserKSettings(db.Model):
    """Per-user K SPA settings stored as JSON blob"""
    __tablename__ = 'user_k_settings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    settings = db.Column(db.JSON, default=dict)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'settings': self.settings or {}
        }


class QrLoginToken(db.Model):
    __tablename__ = 'qr_login_tokens'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    consumed = db.Column(db.Boolean, default=False)
    consumed_at = db.Column(db.DateTime, nullable=True)
    authorized_by_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)

    user = db.relationship('User', backref='qr_login_tokens', lazy=True, foreign_keys=[user_id])
    authorized_by = db.relationship('User', backref='qr_authorized_tokens', lazy=True, foreign_keys=[authorized_by_id])


class LoginOtp(db.Model):
    __tablename__ = 'login_otps'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)

    user = db.relationship('User', backref='login_otps', lazy=True)
