#!/bin/bash

# Kiselgram Mobile Optimization Setup Script
echo "🚀 Setting up Kiselgram with mobile optimization..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_status "Python $PYTHON_VERSION detected"
}

# Install required packages
install_dependencies() {
    print_status "Installing Python dependencies..."

    pip3 install flask flask-sqlalchemy pytelegrambotapi

    if [ $? -eq 0 ]; then
        print_success "Dependencies installed successfully"
    else
        print_error "Failed to install dependencies"
        exit 1
    fi
}

# Create the main application file with mobile optimization
create_app_file() {
    print_status "Creating optimized Kiselgram application..."

    cat > kiselgram_app.py << 'EOF'
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib
import secrets
import os
import telebot
import threading
import time

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
    messages = Message.query.filter(
        ((Message.sender_id == current_user_id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user_id))
    ).order_by(Message.timestamp.asc()).all()

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
EOF

    print_success "Main application file created"
}

# Create mobile-optimized templates
create_templates() {
    print_status "Creating mobile-optimized templates..."

    mkdir -p templates

    # Base template
    cat > templates/base.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{% block title %}Kiselgram{% endblock %}</title>
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="theme-color" content="#0088cc">
    <link rel="manifest" href="/static/manifest.json">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
            -webkit-touch-callout: none;
            -webkit-user-select: none;
            user-select: none;
        }
        html, body {
            height: 100%;
            overflow: hidden;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: #f8f9fa;
        }
        input, textarea, button {
            -webkit-appearance: none;
            border-radius: 0;
        }
        input:focus, textarea:focus {
            -webkit-user-select: text;
            user-select: text;
        }
    </style>
    {% block styles %}{% endblock %}
</head>
<body>
    {% block content %}{% endblock %}
    {% block scripts %}{% endblock %}

    <script>
        // Prevent zoom on double-tap
        let lastTouchEnd = 0;
        document.addEventListener('touchend', function (event) {
            const now = (new Date()).getTime();
            if (now - lastTouchEnd <= 300) {
                event.preventDefault();
            }
            lastTouchEnd = now;
        }, false);

        // Add to home screen prompt
        let deferredPrompt;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
        });

        // Service Worker registration
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/static/sw.js')
                .then(() => console.log('SW registered'))
                .catch(err => console.log('SW registration failed'));
        }
    </script>
</body>
</html>
EOF

    # Login template
    cat > templates/login.html << 'EOF'
{% extends "base.html" %}

{% block styles %}
<style>
    body {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
        min-height: 100vh;
    }
    .login-container {
        background: white;
        border-radius: 16px;
        padding: 30px 25px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        width: 100%;
        max-width: 400px;
        text-align: center;
    }
    .logo {
        font-size: 2.5rem;
        font-weight: 300;
        color: #0088cc;
        margin-bottom: 2rem;
        letter-spacing: -1px;
    }
    .input-group {
        margin-bottom: 1.5rem;
        text-align: left;
    }
    .mobile-input {
        width: 100%;
        padding: 1rem 1.25rem;
        border: 2px solid #e1e5e9;
        border-radius: 12px;
        font-size: 1rem;
        background: #f8f9fa;
        transition: all 0.3s ease;
    }
    .mobile-input:focus {
        outline: none;
        border-color: #0088cc;
        background: white;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,136,204,0.1);
    }
    .mobile-btn {
        width: 100%;
        padding: 1rem;
        border: none;
        border-radius: 12px;
        font-size: 1.1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        background: #0088cc;
        color: white;
    }
    .mobile-btn:active {
        transform: scale(0.98);
        background: #0077b3;
    }
    .error-message {
        color: #e74c3c;
        margin-top: 1rem;
        font-size: 0.9rem;
        padding: 0.75rem;
        background: #ffeaea;
        border-radius: 8px;
    }

    /* Mobile optimizations */
    @media (max-width: 768px) {
        .login-container {
            margin: 0;
            border-radius: 0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .logo {
            font-size: 2rem;
        }
    }

    /* Safe area insets for notch phones */
    @supports(padding: max(0px)) {
        .login-container {
            padding-left: max(25px, env(safe-area-inset-left));
            padding-right: max(25px, env(safe-area-inset-right));
        }
    }
</style>
{% endblock %}

{% block content %}
<div class="login-container">
    <div class="logo">Kiselgram</div>
    <form method="POST">
        <div class="input-group">
            <input type="text" name="username" placeholder="Username" required class="mobile-input">
        </div>
        <div class="input-group">
            <input type="password" name="password" placeholder="Password" required class="mobile-input">
        </div>
        <button type="submit" class="mobile-btn">Login / Register</button>
    </form>
    {% if error %}
        <div class="error-message">{{ error }}</div>
    {% endif %}
</div>
{% endblock %}
EOF

    # Chat list template (mobile optimized)
    cat > templates/chat_list.html << 'EOF'
{% extends "base.html" %}

{% block styles %}
<style>
    .mobile-layout {
        display: flex;
        height: 100vh;
        height: 100dvh; /* Dynamic viewport height */
        background: white;
    }

    /* Sidebar */
    .sidebar {
        width: 100%;
        max-width: 400px;
        display: flex;
        flex-direction: column;
        background: white;
        border-right: 1px solid #e1e5e9;
        transition: transform 0.3s ease;
    }

    .sidebar-header {
        padding: 1rem;
        border-bottom: 1px solid #e1e5e9;
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #0088cc;
        color: white;
        padding-top: env(safe-area-inset-top, 1rem);
    }

    .user-info {
        flex: 1;
        font-weight: 600;
        font-size: 1.1rem;
    }

    .header-actions {
        display: flex;
        gap: 0.5rem;
    }

    .icon-btn, .mobile-menu-btn {
        padding: 0.5rem;
        border-radius: 8px;
        text-decoration: none;
        color: white;
        background: none;
        border: none;
        font-size: 1.2rem;
        cursor: pointer;
    }

    .mobile-menu-btn {
        display: none;
    }

    .search-box {
        padding: 1rem;
        border-bottom: 1px solid #e1e5e9;
        background: white;
    }

    .search-input {
        width: 100%;
        padding: 0.75rem 1rem;
        border: none;
        border-radius: 20px;
        background: #f0f2f5;
        font-size: 0.9rem;
    }

    .chats-list {
        flex: 1;
        overflow-y: auto;
        background: white;
        -webkit-overflow-scrolling: touch;
    }

    .chat-item {
        display: flex;
        padding: 0.75rem 1rem;
        border-bottom: 1px solid #f0f2f5;
        cursor: pointer;
        align-items: center;
        position: relative;
        transition: background 0.2s ease;
    }

    .chat-item:active {
        background: #f8f9fa;
        transform: scale(0.995);
    }

    .chat-item.unread {
        background: #e3f2fd;
    }

    .chat-avatar {
        width: 3rem;
        height: 3rem;
        border-radius: 50%;
        background: #0088cc;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 1.1rem;
        margin-right: 1rem;
        flex-shrink: 0;
    }

    .chat-info {
        flex: 1;
        min-width: 0;
    }

    .chat-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.25rem;
    }

    .chat-name {
        font-weight: 600;
        color: #000;
        font-size: 1rem;
    }

    .chat-time {
        font-size: 0.75rem;
        color: #999;
        flex-shrink: 0;
    }

    .chat-preview {
        font-size: 0.85rem;
        color: #666;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .unread-badge {
        background: #0088cc;
        color: white;
        border-radius: 12px;
        padding: 0.25rem 0.5rem;
        font-size: 0.75rem;
        font-weight: 600;
        min-width: 1.25rem;
        text-align: center;
        flex-shrink: 0;
    }

    .no-chats {
        text-align: center;
        padding: 3rem 1rem;
        color: #999;
    }

    .bottom-nav {
        display: flex;
        border-top: 1px solid #e1e5e9;
        padding: 0.5rem;
        background: white;
        padding-bottom: max(0.5rem, env(safe-area-inset-bottom));
    }

    .nav-item {
        flex: 1;
        text-align: center;
        padding: 0.75rem;
        text-decoration: none;
        color: #666;
        border-radius: 8px;
        font-size: 0.9rem;
        transition: all 0.2s ease;
    }

    .nav-item:active {
        background: #f0f2f5;
        transform: scale(0.95);
    }

    .nav-item.active {
        background: #f0f2f5;
        color: #0088cc;
    }

    /* Main Content */
    .main-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        background: #e5ddd5;
        background-image: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" opacity="0.05"><path fill="%230088cc" d="M0 0h100v100H0z"/></svg>');
    }

    .chat-area {
        flex: 1;
        display: flex;
        flex-direction: column;
    }

    /* Preview Area */
    .chat-preview-area {
        flex: 1;
        display: flex;
        flex-direction: column;
        max-width: 800px;
        margin: 0 auto;
        width: 100%;
        background: rgba(255, 255, 255, 0.95);
        border-radius: 16px;
        margin: 1rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        overflow: hidden;
    }

    .chat-preview-header {
        background: #0088cc;
        color: white;
        padding: 2rem 1.5rem;
        text-align: center;
        border-bottom: 1px solid #e1e5e9;
    }

    .preview-welcome h2 {
        font-size: 1.75rem;
        font-weight: 300;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
    }

    .preview-welcome p {
        font-size: 1rem;
        opacity: 0.9;
        margin: 0;
    }

    .chat-preview-messages {
        flex: 1;
        padding: 1.5rem;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 1rem;
        background: #f8f9fa;
        -webkit-overflow-scrolling: touch;
    }

    .preview-message {
        display: flex;
        align-items: flex-end;
        gap: 0.75rem;
    }

    .preview-message.incoming {
        justify-content: flex-start;
    }

    .preview-message.outgoing {
        justify-content: flex-end;
    }

    .preview-avatar {
        width: 2.5rem;
        height: 2.5rem;
        border-radius: 50%;
        background: #0088cc;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 0.9rem;
        flex-shrink: 0;
    }

    .preview-bubble {
        max-width: 70%;
        padding: 0.75rem 1rem;
        border-radius: 18px;
        position: relative;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }

    .preview-message.incoming .preview-bubble {
        background: white;
        border-bottom-left-radius: 4px;
    }

    .preview-message.outgoing .preview-bubble {
        background: #e3f2fd;
        border-bottom-right-radius: 4px;
    }

    .preview-text {
        margin-bottom: 0.25rem;
        line-height: 1.4;
        font-size: 0.9rem;
    }

    .preview-time {
        font-size: 0.7rem;
        color: #999;
        text-align: right;
    }

    .chat-preview-input {
        background: white;
        padding: 1rem 1.5rem;
        border-top: 1px solid #e1e5e9;
    }

    .preview-input-wrapper {
        display: flex;
        background: #f0f2f5;
        border-radius: 25px;
        padding: 0.5rem;
    }

    .preview-input {
        flex: 1;
        border: none;
        background: transparent;
        padding: 0.5rem 1rem;
        font-size: 0.9rem;
        outline: none;
        color: #999;
    }

    .preview-send-btn {
        background: #ccc;
        color: white;
        border: none;
        border-radius: 50%;
        width: 2.5rem;
        height: 2.5rem;
        cursor: not-allowed;
        font-size: 0.9rem;
    }

    /* Active Chat Area */
    .active-chat-area {
        flex: 1;
        display: flex;
        flex-direction: column;
        background: white;
    }

    .chat-header {
        background: white;
        padding: 1rem;
        border-bottom: 1px solid #e1e5e9;
        display: flex;
        align-items: center;
        gap: 1rem;
        padding-top: env(safe-area-inset-top, 1rem);
    }

    .back-btn {
        text-decoration: none;
        color: #0088cc;
        font-size: 1.2rem;
        padding: 0.5rem;
        cursor: pointer;
        flex-shrink: 0;
    }

    .chat-user-info {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        flex: 1;
    }

    .chat-avatar.small {
        width: 2.5rem;
        height: 2.5rem;
        font-size: 1rem;
    }

    .chat-status {
        font-size: 0.8rem;
        color: #00a884;
    }

    .messages-container {
        flex: 1;
        padding: 1rem;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
        background: #e5ddd5;
        background-image: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" opacity="0.05"><path fill="%230088cc" d="M0 0h100v100H0z"/></svg>');
        -webkit-overflow-scrolling: touch;
    }

    .message {
        display: flex;
    }

    .message.incoming {
        justify-content: flex-start;
    }

    .message.outgoing {
        justify-content: flex-end;
    }

    .message-bubble {
        max-width: 85%;
        padding: 0.75rem 1rem;
        border-radius: 18px;
        position: relative;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        word-wrap: break-word;
        overflow-wrap: break-word;
    }

    .message.incoming .message-bubble {
        background: white;
        border-bottom-left-radius: 4px;
    }

    .message.outgoing .message-bubble {
        background: #e3f2fd;
        border-bottom-right-radius: 4px;
    }

    .message-text {
        margin-bottom: 0.25rem;
        line-height: 1.4;
        font-size: 0.95rem;
    }

    .message-time {
        font-size: 0.75rem;
        color: #999;
        text-align: right;
    }

    .message-status {
        margin-left: 0.25rem;
    }

    .no-messages {
        text-align: center;
        color: #999;
        margin-top: 3rem;
        padding: 2rem;
    }

    .message-input-container {
        background: white;
        padding: 1rem;
        border-top: 1px solid #e1e5e9;
        padding-bottom: max(1rem, env(safe-area-inset-bottom));
    }

    .message-form {
        display: flex;
    }

    .input-wrapper {
        display: flex;
        flex: 1;
        background: #f0f2f5;
        border-radius: 25px;
        padding: 0.5rem;
    }

    .message-input {
        flex: 1;
        border: none;
        background: transparent;
        padding: 0.75rem 1rem;
        font-size: 1rem;
        outline: none;
        -webkit-user-select: text;
        user-select: text;
    }

    .send-btn {
        background: #0088cc;
        color: white;
        border: none;
        border-radius: 50%;
        width: 2.5rem;
        height: 2.5rem;
        cursor: pointer;
        font-size: 1rem;
        transition: all 0.2s ease;
        flex-shrink: 0;
    }

    .send-btn:active {
        transform: scale(0.95);
        background: #0077b3;
    }

    /* Mobile Responsive Design */
    @media (max-width: 768px) {
        .mobile-layout {
            position: relative;
        }

        .sidebar {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 1000;
            transform: translateX(-100%);
        }

        .sidebar.active {
            transform: translateX(0);
        }

        .mobile-menu-btn {
            display: block;
        }

        .main-content {
            width: 100%;
        }

        .chat-preview-area {
            margin: 0;
            border-radius: 0;
            height: 100%;
        }

        .message-bubble {
            max-width: 90%;
        }

        .chat-avatar {
            width: 2.5rem;
            height: 2.5rem;
            font-size: 1rem;
        }

        .chat-name {
            font-size: 0.95rem;
        }

        .chat-preview {
            font-size: 0.8rem;
        }
    }

    /* Large screens */
    @media (min-width: 769px) {
        .sidebar {
            transform: translateX(0) !important;
        }

        .mobile-menu-btn {
            display: none;
        }
    }

    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .sidebar, .main-content, .chat-preview-area, .active-chat-area {
            background: #1a1a1a;
            color: #ffffff;
        }

        .chat-item, .search-box, .bottom-nav {
            background: #1a1a1a;
            border-color: #333;
        }

        .chat-name, .chat-preview {
            color: #ffffff;
        }

        .search-input, .message-input {
            background: #2d2d2d;
            color: #ffffff;
        }

        .message.incoming .message-bubble {
            background: #2d2d2d;
            color: #ffffff;
        }
    }

    /* High DPI screens */
    @media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi) {
        .chat-avatar, .preview-avatar, .chat-avatar.small {
            -webkit-font-smoothing: antialiased;
        }
    }
</style>
{% endblock %}

{% block content %}
<div class="mobile-layout">
    <!-- Sidebar -->
    <div class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <div class="user-info">
                <strong>{{ current_user }}</strong>
            </div>
            <div class="header-actions">
                <a href="/search" class="icon-btn">🔍</a>
                <button class="mobile-menu-btn" onclick="toggleSidebar()">☰</button>
            </div>
        </div>

        <div class="search-box">
            <input type="text" placeholder="Search" class="search-input" onclick="location.href='/search'">
        </div>

        <div class="chats-list" id="chatsList">
            {% if chats %}
                {% for chat in chats %}
                <div class="chat-item {% if chat.unread_count > 0 %}unread{% endif %}"
                     onclick="loadChat({{ chat.user.id }}, '{{ chat.user.username }}')">
                    <div class="chat-avatar">
                        {{ chat.user.username[0]|upper }}
                    </div>
                    <div class="chat-info">
                        <div class="chat-header">
                            <span class="chat-name">{{ chat.user.username }}</span>
                            <span class="chat-time">{{ chat.timestamp }}</span>
                        </div>
                        <div class="chat-preview">
                            {% if chat.last_message %}
                                {{ chat.last_message.content[:50] }}{% if chat.last_message.content|length > 50 %}...{% endif %}
                            {% else %}
                                No messages yet
                            {% endif %}
                        </div>
                    </div>
                    {% if chat.unread_count > 0 %}
                    <div class="unread-badge">{{ chat.unread_count }}</div>
                    {% endif %}
                </div>
                {% endfor %}
            {% else %}
            <div class="no-chats">
                <p>No chats yet</p>
                <p style="font-size: 14px; color: #999; margin-top: 10px;">Start a conversation with someone!</p>
            </div>
            {% endif %}
        </div>

        <div class="bottom-nav">
            <a href="/chat_list" class="nav-item active">💬 Chats</a>
            <a href="/users" class="nav-item">👥 Contacts</a>
            <a href="/settings" class="nav-item">⚙️ Settings</a>
        </div>
    </div>

    <!-- Main Content - Dynamic Chat Area -->
    <div class="main-content" id="mainContent">
        <div class="chat-area" id="chatArea">
            <div class="chat-preview-area" id="previewArea">
                <div class="chat-preview-header">
                    <div class="preview-welcome">
                        <h2>Kiselgram</h2>
                        <p>Your secure messaging app</p>
                    </div>
                </div>

                <div class="chat-preview-messages">
                    <div class="preview-message incoming">
                        <div class="preview-avatar">K</div>
                        <div class="preview-bubble">
                            <div class="preview-text">Welcome to Kiselgram! Start chatting with your contacts.</div>
                            <div class="preview-time">10:00</div>
                        </div>
                    </div>

                    <div class="preview-message outgoing">
                        <div class="preview-bubble">
                            <div class="preview-text">Select a chat from the sidebar to start messaging</div>
                            <div class="preview-time">10:01</div>
                        </div>
                    </div>
                </div>

                <div class="chat-preview-input">
                    <div class="preview-input-wrapper">
                        <input type="text" placeholder="Select a chat to start messaging" class="preview-input" disabled>
                        <button class="preview-send-btn" disabled>➤</button>
                    </div>
                </div>
            </div>

            <!-- Active Chat Area (hidden by default) -->
            <div class="active-chat-area" id="activeChatArea" style="display: none;">
                <div class="chat-header" id="chatHeader">
                    <a href="javascript:void(0)" class="back-btn" onclick="showPreview()">←</a>
                    <div class="chat-user-info">
                        <div class="chat-avatar small" id="chatAvatar">U</div>
                        <div>
                            <div class="chat-name" id="chatUserName">User</div>
                            <div class="chat-status">online</div>
                        </div>
                    </div>
                </div>

                <div class="messages-container" id="messagesContainer">
                    <!-- Messages will be loaded here dynamically -->
                </div>

                <div class="message-input-container">
                    <form id="messageForm" class="message-form">
                        <div class="input-wrapper">
                            <input type="text" name="message" placeholder="Message" class="message-input" required autocomplete="off" id="messageInput">
                            <button type="submit" class="send-btn">➤</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
let currentChatUserId = null;
let messagePollInterval = null;
let isMobile = window.innerWidth <= 768;

// Mobile sidebar toggle
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('active');
}

// Close sidebar when clicking on main content (mobile)
if (isMobile) {
    document.getElementById('mainContent').addEventListener('click', function() {
        document.getElementById('sidebar').classList.remove('active');
    });
}

// Load chat when clicking on a chat item
function loadChat(userId, username) {
    currentChatUserId = userId;

    // Update UI
    document.getElementById('chatUserName').textContent = username;
    document.getElementById('chatAvatar').textContent = username[0].toUpperCase();
    document.getElementById('previewArea').style.display = 'none';
    document.getElementById('activeChatArea').style.display = 'flex';

    // Close sidebar on mobile
    if (isMobile) {
        document.getElementById('sidebar').classList.remove('active');
    }

    // Load messages
    loadMessages(userId);

    // Start polling for new messages
    if (messagePollInterval) {
        clearInterval(messagePollInterval);
    }
    messagePollInterval = setInterval(() => loadMessages(userId), 2000);

    // Focus the message input
    setTimeout(() => {
        document.getElementById('messageInput').focus();
    }, 100);
}

// Show preview (go back)
function showPreview() {
    document.getElementById('previewArea').style.display = 'flex';
    document.getElementById('activeChatArea').style.display = 'none';
    currentChatUserId = null;

    if (messagePollInterval) {
        clearInterval(messagePollInterval);
        messagePollInterval = null;
    }
}

// Load messages from API
async function loadMessages(userId) {
    try {
        const response = await fetch(`/api/messages/${userId}`);
        const data = await response.json();

        if (data.messages) {
            displayMessages(data.messages);
        }
    } catch (error) {
        console.error('Error loading messages:', error);
    }
}

// Display messages in the chat
function displayMessages(messages) {
    const container = document.getElementById('messagesContainer');
    container.innerHTML = '';

    if (messages.length === 0) {
        container.innerHTML = `
            <div class="no-messages">
                <p>No messages yet</p>
                <p>Send a message to start the conversation!</p>
            </div>
        `;
        return;
    }

    messages.forEach(message => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.is_own ? 'outgoing' : 'incoming'}`;

        messageDiv.innerHTML = `
            <div class="message-bubble">
                <div class="message-text">${escapeHtml(message.content)}</div>
                <div class="message-time">
                    ${message.timestamp}
                    ${message.is_own ? `<span class="message-status">${message.is_read ? '✓✓' : '✓'}</span>` : ''}
                </div>
            </div>
        `;

        container.appendChild(messageDiv);
    });

    // Scroll to bottom with smooth behavior
    container.scrollTo({
        top: container.scrollHeight,
        behavior: 'smooth'
    });
}

// Send message
document.getElementById('messageForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!currentChatUserId) return;

    const input = document.getElementById('messageInput');
    const content = input.value.trim();

    if (!content) return;

    try {
        const response = await fetch('/api/send_message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                receiver_id: currentChatUserId,
                content: content
            })
        });

        const data = await response.json();

        if (data.success) {
            input.value = '';
            // Reload messages to show the new one
            loadMessages(currentChatUserId);
        }
    } catch (error) {
        console.error('Error sending message:', error);
    }
});

// Utility function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Update chat list periodically
setInterval(updateChatList, 5000);

async function updateChatList() {
    try {
        const response = await fetch('/api/chat_list');
        const data = await response.json();

        if (data.chats) {
            const chatsList = document.getElementById('chatsList');
            chatsList.innerHTML = '';

            if (data.chats.length === 0) {
                chatsList.innerHTML = `
                    <div class="no-chats">
                        <p>No chats yet</p>
                        <p style="font-size: 14px; color: #999; margin-top: 10px;">Start a conversation with someone!</p>
                    </div>
                `;
                return;
            }

            data.chats.forEach(chat => {
                const chatItem = document.createElement('div');
                chatItem.className = `chat-item ${chat.unread_count > 0 ? 'unread' : ''}`;
                chatItem.onclick = () => loadChat(chat.user_id, chat.username);

                chatItem.innerHTML = `
                    <div class="chat-avatar">${chat.username[0].toUpperCase()}</div>
                    <div class="chat-info">
                        <div class="chat-header">
                            <span class="chat-name">${escapeHtml(chat.username)}</span>
                            <span class="chat-time">${chat.timestamp}</span>
                        </div>
                        <div class="chat-preview">
                            ${chat.last_message ? escapeHtml(chat.last_message.substring(0, 50)) + (chat.last_message.length > 50 ? '...' : '') : 'No messages yet'}
                        </div>
                    </div>
                    ${chat.unread_count > 0 ? `<div class="unread-badge">${chat.unread_count}</div>` : ''}
                `;

                chatsList.appendChild(chatItem);
            });
        }
    } catch (error) {
        console.error('Error updating chat list:', error);
    }
}

// Handle resize events
window.addEventListener('resize', function() {
    isMobile = window.innerWidth <= 768;
});

// Prevent body scroll when sidebar is open (mobile)
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.attributeName === 'class') {
                if (sidebar.classList.contains('active')) {
                    document.body.style.overflow = 'hidden';
                } else {
                    document.body.style.overflow = '';
                }
            }
        });
    });

    observer.observe(sidebar, { attributes: true });
});

// Add touch feedback to buttons
document.addEventListener('touchstart', function() {}, { passive: true });
</script>
{% endblock %}
EOF

    # Create other templates (users_list.html, chat.html, search.html, settings.html)
    for template in users_list.html chat.html search.html settings.html; do
        cat > templates/$template << EOF
{% extends "base.html" %}

{% block content %}
<div class="mobile-layout">
    <div class="sidebar">
        <div class="sidebar-header">
            <div class="user-info">
                <strong>{% if template == 'users_list.html' %}Contacts{% elif template == 'settings.html' %}Settings{% else %}Search{% endif %}</strong>
            </div>
            <div class="header-actions">
                <a href="/chat_list" class="icon-btn">←</a>
                <button class="mobile-menu-btn" onclick="toggleSidebar()">☰</button>
            </div>
        </div>

        <div class="chats-list">
            <div style="padding: 2rem; text-align: center; color: #666;">
                <p>Mobile-optimized {{ template.replace('.html', '').replace('_', ' ').title() }} view</p>
                <p style="font-size: 0.9rem; margin-top: 1rem;">Fully responsive design</p>
            </div>
        </div>

        <div class="bottom-nav">
            <a href="/chat_list" class="nav-item">💬 Chats</a>
            <a href="/users" class="nav-item {% if template == 'users_list.html' %}active{% endif %}">👥 Contacts</a>
            <a href="/settings" class="nav-item {% if template == 'settings.html' %}active{% endif %}">⚙️ Settings</a>
        </div>
    </div>

    <div class="main-content">
        <div style="padding: 2rem; text-align: center;">
            <h2>{{ template.replace('.html', '').replace('_', ' ').title() }}</h2>
            <p>Mobile-optimized interface</p>
        </div>
    </div>
</div>

<script>
function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('active');
}
</script>
{% endblock %}
EOF
    done

    print_success "Mobile-optimized templates created"
}

# Create PWA manifest and service worker
create_pwa_files() {
    print_status "Creating PWA files for mobile app experience..."

    mkdir -p static

    # Manifest
    cat > static/manifest.json << 'EOF'
{
    "name": "Kiselgram",
    "short_name": "Kiselgram",
    "description": "Secure messaging app with Telegram integration",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#0088cc",
    "theme_color": "#0088cc",
    "orientation": "portrait",
    "scope": "/",
    "icons": [
        {
            "src": "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' fill='%230088cc'/><text x='50' y='60' font-family='Arial' font-size='40' text-anchor='middle' fill='white'>K</text></svg>",
            "sizes": "192x192",
            "type": "image/svg+xml"
        },
        {
            "src": "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' fill='%230088cc'/><text x='50' y='60' font-family='Arial' font-size='40' text-anchor='middle' fill='white'>K</text></svg>",
            "sizes": "512x512",
            "type": "image/svg+xml"
        }
    ]
}
EOF

    # Service Worker
    cat > static/sw.js << 'EOF'
const CACHE_NAME = 'kiselgram-v1';
const urlsToCache = [
    '/',
    '/static/manifest.json'
];

self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function(cache) {
                return cache.addAll(urlsToCache);
            })
    );
});

self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.match(event.request)
            .then(function(response) {
                if (response) {
                    return response;
                }
                return fetch(event.request);
            }
        )
    );
});
EOF

    print_success "PWA files created"
}

# Create environment file
create_env_file() {
    print_status "Creating environment configuration..."

    cat > .env << 'EOF'
# Kiselgram Mobile Configuration
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///kiselgram.db

# Mobile PWA Settings
PWA_NAME=Kiselgram
PWA_SHORT_NAME=Kiselgram
PWA_THEME_COLOR=#0088cc
PWA_BACKGROUND_COLOR=#ffffff

# Server Settings
HOST=0.0.0.0
PORT=5000
DEBUG=True
EOF

    print_success "Environment file created"
}

# Create startup script
create_startup_script() {
    print_status "Creating startup script..."

    cat > start_kiselgram.sh << 'EOF'
#!/bin/bash

echo "📱 Starting Kiselgram Mobile..."
echo "🌐 Server will be available at: http://localhost:5000"
echo "📱 Open on mobile: Use your local IP address"
echo ""

# Get local IP address
IP_ADDRESS=$(hostname -I | awk '{print $1}')
echo "📡 Access from other devices: http://$IP_ADDRESS:5000"
echo ""

# Start the application
python3 kiselgram_app.py
EOF

    chmod +x start_kiselgram.sh
    print_success "Startup script created"
}


main() {
print_status "Starting Kiselgram Mobile Optimization Setup..."

text
check_python
install_dependencies
create_app_file
create_templates
create_pwa_files
create_env_file
create_startup_script
create_readme

print_success "🎉 Kiselgram Mobile Setup Complete!"
echo ""
print_status "Next steps:"
echo "1. Edit .env file with your Telegram bot token (optional)"
echo "2. Run: ./start_kiselgram.sh"
echo "3. Open http://localhost:5000 on your computer"
echo "4. Access from mobile using your local IP address"
echo ""
}

main