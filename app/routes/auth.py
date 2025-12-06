from flask import Blueprint, render_template, request, redirect, url_for, session
from app import db
from app.models import User
from app.utils.helpers import hash_password, get_current_user, get_current_user_id

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/', methods=['GET', 'POST'])
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

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@auth_bp.route('/settings')
def settings():
    if not get_current_user():
        return redirect('/')

    user = User.query.get(get_current_user_id())
    return render_template('settings.html', current_user=get_current_user(), user=user)