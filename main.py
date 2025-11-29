from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib
import secrets
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kiselgram.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy=True)
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy=True)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)


# Utility functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def get_current_user():
    return session.get('username')


def get_current_user_id():
    return session.get('user_id')


# Routes
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template('login.html', error="Username and password are required")

        # Hash the password
        password_hash = hash_password(password)

        # Check if user exists
        user = User.query.filter_by(username=username).first()

        if user:
            # Verify password
            if user.password_hash == password_hash:
                session['username'] = username
                session['user_id'] = user.id
                return redirect('/chat_list')
            else:
                return render_template('login.html', error="Invalid password")
        else:
            # Create new user
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

    # Get all users that the current user has chatted with
    sent_chats = db.session.query(Message.receiver_id).filter_by(sender_id=current_user_id).distinct()
    received_chats = db.session.query(Message.sender_id).filter_by(receiver_id=current_user_id).distinct()

    chat_user_ids = set([id[0] for id in sent_chats] + [id[0] for id in received_chats])

    chats_data = []
    for user_id in chat_user_ids:
        user = User.query.get(user_id)
        if user:
            # Get last message
            last_message = Message.query.filter(
                ((Message.sender_id == current_user_id) & (Message.receiver_id == user_id)) |
                ((Message.sender_id == user_id) & (Message.receiver_id == current_user_id))
            ).order_by(Message.timestamp.desc()).first()

            # Count unread messages
            unread_count = Message.query.filter_by(
                sender_id=user_id,
                receiver_id=current_user_id,
                is_read=False
            ).count()

            # Format timestamp
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

    # Sort by last message timestamp
    chats_data.sort(key=lambda x: x['last_message'].timestamp if x['last_message'] else datetime.min, reverse=True)

    return render_template(
        'chat_list.html',
        current_user=get_current_user(),
        chats=chats_data
    )


@app.route('/users')
def users_list():
    if not get_current_user():
        return redirect('/')

    users = User.query.all()
    return render_template(
        'users_list.html',
        current_user=get_current_user(),
        users=users
    )


@app.route('/chat/<int:user_id>', methods=['GET', 'POST'])
def chat(user_id):
    if not get_current_user():
        return redirect('/')

    current_user_id = get_current_user_id()
    receiver = User.query.get_or_404(user_id)

    if request.method == 'POST':
        content = request.form.get('message')
        if content and content.strip():
            new_message = Message(
                content=content.strip(),
                sender_id=current_user_id,
                receiver_id=user_id
            )
            db.session.add(new_message)
            db.session.commit()
            return redirect(f'/chat/{user_id}')

    # Get messages between current user and the other user
    messages = Message.query.filter(
        ((Message.sender_id == current_user_id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current_user_id))
    ).order_by(Message.timestamp.asc()).all()

    # Mark received messages as read
    unread_messages = Message.query.filter_by(
        sender_id=user_id,
        receiver_id=current_user_id,
        is_read=False
    ).all()

    for message in unread_messages:
        message.is_read = True
    db.session.commit()

    return render_template(
        'chat.html',
        current_user=get_current_user(),
        receiver=receiver,
        messages=messages
    )


@app.route('/search')
def search():
    if not get_current_user():
        return redirect('/')

    query = request.args.get('q', '')
    users = []

    if query:
        users = User.query.filter(User.username.ilike(f'%{query}%')).all()

    return render_template(
        'search.html',
        current_user=get_current_user(),
        users=users,
        query=query
    )


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# Initialize database
def init_db():
    with app.app_context():
        db.create_all()


if __name__ == '__main__':
    init_db()
    print("Kiselgram is running on http://localhost:5000")
    print("Database initialized: kiselgram.db")
    app.run(debug=True, host='0.0.0.0', port=5000)