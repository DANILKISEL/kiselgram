from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from app import db
from app.models import Channel, ChannelSubscriber, Message
from app.utils.helpers import get_current_user, get_current_user_id, generate_invite_link

channels_bp = Blueprint('channels', __name__)

@channels_bp.route('/create_channel', methods=['GET', 'POST'])
def create_channel():
    if not get_current_user():
        return redirect('/')

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        is_public = request.form.get('is_public') == 'on'

        if not name:
            return render_template('create_channel.html', error="Channel name is required")

        try:
            invite_link = generate_invite_link()
            new_channel = Channel(
                name=name,
                description=description,
                owner_id=get_current_user_id(),
                is_public=is_public,
                invite_link=invite_link
            )
            db.session.add(new_channel)
            db.session.flush()

            # Add creator as subscriber
            subscription = ChannelSubscriber(
                user_id=get_current_user_id(),
                channel_id=new_channel.id
            )
            db.session.add(subscription)
            db.session.commit()

            return redirect(f'/channel/{new_channel.id}')
        except Exception as e:
            db.session.rollback()
            return render_template('create_channel.html', error="Error creating channel")

    return render_template('create_channel.html')

@channels_bp.route('/channel/<int:channel_id>')
def channel_view(channel_id):
    if not get_current_user():
        return redirect('/')

    channel = Channel.query.get_or_404(channel_id)
    subscription = ChannelSubscriber.query.filter_by(user_id=get_current_user_id(), channel_id=channel_id).first()
    if not subscription:
        return redirect('/join_channel/' + channel.invite_link)

    return render_template('channel.html', current_user=get_current_user(), channel=channel)

@channels_bp.route('/join_channel/<invite_link>')
def join_channel(invite_link):
    if not get_current_user():
        return redirect('/')

    channel = Channel.query.filter_by(invite_link=invite_link).first_or_404()

    existing_subscriber = ChannelSubscriber.query.filter_by(user_id=get_current_user_id(),
                                                            channel_id=channel.id).first()
    if existing_subscriber:
        return redirect(f'/channel/{channel.id}')

    try:
        subscription = ChannelSubscriber(
            user_id=get_current_user_id(),
            channel_id=channel.id
        )
        db.session.add(subscription)
        db.session.commit()
        return redirect(f'/channel/{channel.id}')
    except:
        db.session.rollback()
        return redirect('/chat_list')

@channels_bp.route('/channel_info/<int:channel_id>')
def channel_info(channel_id):
    if not get_current_user():
        return redirect('/')

    channel = Channel.query.get_or_404(channel_id)
    subscription = ChannelSubscriber.query.filter_by(user_id=get_current_user_id(), channel_id=channel_id).first()
    if not subscription:
        return redirect('/join_channel/' + channel.invite_link)

    subscribers = ChannelSubscriber.query.filter_by(channel_id=channel_id).all()
    return render_template('channel_info.html', current_user=get_current_user(), channel=channel,
                           subscribers=subscribers)

@channels_bp.route('/leave_channel/<int:channel_id>')
def leave_channel(channel_id):
    if not get_current_user():
        return redirect('/')

    subscription = ChannelSubscriber.query.filter_by(user_id=get_current_user_id(), channel_id=channel_id).first()
    if subscription:
        db.session.delete(subscription)
        db.session.commit()

    return redirect('/chat_list')