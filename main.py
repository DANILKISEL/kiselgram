from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib
import secrets
import os
import telebot
import threading
import time
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'kiselgram-mobile-optimized-' + secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kiselgram.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN) if TELEGRAM_BOT_TOKEN != 'YOUR_BOT_TOKEN_HERE' else None

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    telegram_chat_id = db.Column(db.String(50), unique=True, nullable=True)
    telegram_username = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy=True)
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    telegram_message_id = db.Column(db.String(50), nullable=True)
    is_from_telegram = db.Column(db.Boolean, default=False)

class TelegramBot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

# Utility functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_current_user():
    return session.get('username')

def get_current_user_id():
    return session.get('user_id')

def setup_bots():
    """Initialize bot users"""
    bots_data = [
        {'name': 'Weather Bot', 'username': 'weather_bot', 'description': 'Get weather information'},
        {'name': 'News Bot', 'username': 'news_bot', 'description': 'Latest news headlines'},
        {'name': 'Calculator Bot', 'username': 'calc_bot', 'description': 'Mathematical calculations'},
        {'name': 'Joke Bot', 'username': 'joke_bot', 'description': 'Random jokes'},
        {'name': 'Kiselgram Help', 'username': 'kiselgram_bot', 'description': 'Official help'}
    ]

    for bot_data in bots_data:
        if not User.query.filter_by(username=bot_data['username']).first():
            bot_user = User(username=bot_data['username'], password_hash=hash_password(secrets.token_hex(16)))
            db.session.add(bot_user)
        if not TelegramBot.query.filter_by(username=bot_data['username']).first():
            telegram_bot = TelegramBot(**bot_data)
            db.session.add(telegram_bot)

    db.session.commit()

# Routes
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template('login.html', error="Username and password are required")

        password_hash = hash_password(password)
        user = User.query.filter_by(username=username).first()

        if user:
            if user.password_hash == password_hash:
                session['username'] = username
                session['user_id'] = user.id
                return redirect('/chat_list')
            else:
                return render_template('login.html', error="Invalid password")
        else:
            try:
                new_user = User(username=username, password_hash=password_hash)
                db.session.add(new_user)
                db.session.commit()
                session['username'] = username
                session['user_id'] = new_user.id
                return redirect('/chat_list')
            except:
                db.session.rollback()
                return render_template('login.html', error="Username already exists")

    return render_template('login.html')

@app.route('/chat_list')
def chat_list():
    if not get_current_user():
        return redirect('/')

    current_user_id = get_current_user_id()

    # Get chats
    sent_chats = db.session.query(Message.receiver_id).filter_by(sender_id=current_user_id).distinct()
    received_chats = db.session.query(Message.sender_id).filter_by(receiver_id=current_user_id).distinct()
    chat_user_ids = set([id[0] for id in sent_chats] + [id[0] for id in received_chats])

    chats_data = []
    for user_id in chat_user_ids:
        user = User.query.get(user_id)
        if user:
            last_message = Message.query.filter(
                ((Message.sender_id == current_user_id) & (Message.receiver_id == user_id)) |
                ((Message.sender_id == user_id) & (Message.receiver_id == current_user_id))
            ).order_by(Message.timestamp.desc()).first()

            unread_count = Message.query.filter_by(sender_id=user_id, receiver_id=current_user_id, is_read=False).count()

            if last_message:
                time_diff = datetime.utcnow() - last_message.timestamp
                if time_diff.days == 0:
                    timestamp = last_message.timestamp.strftime('%H:%M')
                elif time_diff.days == 1:
                    timestamp = 'Yesterday'
                elif time_diff.days < 7:
                    timestamp = last_message.timestamp.strftime('%A')
                else:
                    timestamp = last_message.timestamp.strftime('%d.%m.%Y')
            else:
                timestamp = ''

            chats_data.append({
                'user': user,
                'last_message': last_message,
                'unread_count': unread_count,
                'timestamp': timestamp
            })

    chats_data.sort(key=lambda x: x['last_message'].timestamp if x['last_message'] else datetime.min, reverse=True)
    bots = TelegramBot.query.filter_by(is_active=True).all()

    return render_template('chat_list.html', current_user=get_current_user(), chats=chats_data, bots=bots)

# API endpoints
@app.route('/api/messages/<int:user_id>')
def api_messages(user_id):
    if not get_current_user():
        return jsonify({'error': 'Not authenticated'}), 401

    current_user_id = get_current_user_id()

    # Get after parameter for incremental loading
    after_id = request.args.get('after', 0, type=int)

    messages = Message.query.filter(
        ((Message.sender_id == current_user_id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user_id))
    ).filter(Message.id > after_id).order_by(Message.timestamp.asc()).all()

    messages_data = []
    for message in messages:
        messages_data.append({
            'id': message.id,
            'content': message.content,
            'sender_name': message.sender.username,
            'timestamp': message.timestamp.strftime('%H:%M'),
            'is_read': message.is_read,
            'is_own': message.sender_id == current_user_id,
        })

    return jsonify({'messages': messages_data})

@app.route('/api/send_message', methods=['POST'])
def api_send_message():
    if not get_current_user():
        return jsonify({'error': 'Not authenticated'}), 401

    current_user_id = get_current_user_id()
    data = request.get_json()
    receiver_id = data.get('receiver_id')
    content = data.get('content')

    if not receiver_id or not content:
        return jsonify({'error': 'Missing parameters'}), 400

    # Create message
    new_message = Message(content=content, sender_id=current_user_id, receiver_id=receiver_id)
    db.session.add(new_message)
    db.session.commit()

    message_data = {
        'id': new_message.id,
        'content': new_message.content,
        'sender_name': new_message.sender.username,
        'timestamp': new_message.timestamp.strftime('%H:%M'),
        'is_own': True,
    }

    return jsonify({'success': True, 'message': message_data})

@app.route('/api/chat_list')
def api_chat_list():
    if not get_current_user():
        return jsonify({'error': 'Not authenticated'}), 401

    current_user_id = get_current_user_id()
    sent_chats = db.session.query(Message.receiver_id).filter_by(sender_id=current_user_id).distinct()
    received_chats = db.session.query(Message.sender_id).filter_by(receiver_id=current_user_id).distinct()
    chat_user_ids = set([id[0] for id in sent_chats] + [id[0] for id in received_chats])

    chats_data = []
    for user_id in chat_user_ids:
        user = User.query.get(user_id)
        if user:
            last_message = Message.query.filter(
                ((Message.sender_id == current_user_id) & (Message.receiver_id == user_id)) |
                ((Message.sender_id == user_id) & (Message.receiver_id == current_user_id))
            ).order_by(Message.timestamp.desc()).first()

            unread_count = Message.query.filter_by(sender_id=user_id, receiver_id=current_user_id, is_read=False).count()

            if last_message:
                time_diff = datetime.utcnow() - last_message.timestamp
                timestamp = last_message.timestamp.strftime('%H:%M') if time_diff.days == 0 else 'Yesterday' if time_diff.days == 1 else last_message.timestamp.strftime('%d.%m.%Y')
            else:
                timestamp = ''

            chats_data.append({
                'user_id': user.id,
                'username': user.username,
                'last_message': last_message.content if last_message else '',
                'unread_count': unread_count,
                'timestamp': timestamp,
            })

    return jsonify({'chats': chats_data})

@app.route('/users')
def users_list():
    if not get_current_user():
        return redirect('/')

    users = User.query.all()
    bots = TelegramBot.query.filter_by(is_active=True).all()
    return render_template('users_list.html', current_user=get_current_user(), users=users, bots=bots)

@app.route('/chat/<int:user_id>')
def chat(user_id):
    if not get_current_user():
        return redirect('/')

    receiver = User.query.get_or_404(user_id)
    # Mark messages as read
    Message.query.filter_by(sender_id=user_id, receiver_id=get_current_user_id(), is_read=False).update({'is_read': True})
    db.session.commit()

    return render_template('chat.html', current_user=get_current_user(), receiver=receiver)

@app.route('/settings')
def settings():
    if not get_current_user():
        return redirect('/')

    user = User.query.get(get_current_user_id())
    return render_template('settings.html', current_user=get_current_user(), user=user)

@app.route('/search')
def search():
    if not get_current_user():
        return redirect('/')

    query = request.args.get('q', '')
    users = User.query.filter(User.username.ilike(f'%{query}%')).all() if query else []
    return render_template('search.html', current_user=get_current_user(), users=users, query=query)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

def init_db():
    with app.app_context():
        db.create_all()
        setup_bots()
        print("Database initialized with mobile optimization")

if __name__ == '__main__':
    init_db()
    print("📱 Kiselgram Mobile Optimized")
    print("🌐 Running on http://localhost:5000")
    print("📱 Optimized for mobile devices")
    app.run(debug=True, host='0.0.0.0', port=5000)
