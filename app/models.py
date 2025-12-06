from app import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    telegram_chat_id = db.Column(db.String(50), unique=True, nullable=True)
    telegram_username = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy=True)
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy=True)
    owned_groups = db.relationship('Group', foreign_keys='Group.owner_id', backref='owner', lazy=True)
    group_memberships = db.relationship('GroupMember', backref='user', lazy=True)
    channel_subscriptions = db.relationship('ChannelSubscriber', backref='user', lazy=True)
    owned_channels = db.relationship('Channel', foreign_keys='Channel.owner_id', backref='owner', lazy=True)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    telegram_message_id = db.Column(db.String(50), nullable=True)
    is_from_telegram = db.Column(db.Boolean, default=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)
    channel_id = db.Column(db.Integer, db.ForeignKey('channel.id'), nullable=True)

    # File attachment fields
    has_attachment = db.Column(db.Boolean, default=False)
    file_type = db.Column(db.String(20), nullable=True)
    file_name = db.Column(db.String(255), nullable=True)
    file_path = db.Column(db.String(500), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    thumbnail_path = db.Column(db.String(500), nullable=True)


class TelegramBot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_public = db.Column(db.Boolean, default=True)
    invite_link = db.Column(db.String(100), unique=True, nullable=True)

    members = db.relationship('GroupMember', backref='group', lazy=True)
    messages = db.relationship('Message', backref='group', lazy=True)


class GroupMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String(20), default='member')

    __table_args__ = (db.UniqueConstraint('user_id', 'group_id', name='unique_group_member'),)


class Channel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_public = db.Column(db.Boolean, default=True)
    invite_link = db.Column(db.String(100), unique=True, nullable=True)

    messages = db.relationship('Message', backref='channel', lazy=True)
    subscribers = db.relationship('ChannelSubscriber', backref='channel', lazy=True)


class ChannelSubscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    channel_id = db.Column(db.Integer, db.ForeignKey('channel.id'), nullable=False)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'channel_id', name='unique_channel_subscriber'),)