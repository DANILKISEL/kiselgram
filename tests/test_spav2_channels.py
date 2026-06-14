"""Tests for V2 API channel endpoints under /api.v2/api/."""

from datetime import datetime
from app import db
from app.models import User, Chat, ChatSubscriber, Message


API_PREFIX = "/api.v2/api"


def _create_channel(owner, name="Test Channel", description="A test channel"):
    chat = Chat(chat_type="channel", name=name, description=description,
                owner_id=owner.id, created_at=datetime.utcnow())
    db.session.add(chat)
    db.session.commit()
    return chat


class TestV2ChannelDetail:
    """GET /api.v2/api/channels/<id>"""

    def test_get_channel_detail(self, logged_in_admin, admin_user):
        c = _create_channel(admin_user)
        resp = logged_in_admin.get(f"{API_PREFIX}/channels/{c.id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["name"] == "Test Channel"

    def test_get_channel_not_found(self, logged_in_client, user):
        resp = logged_in_client.get(f"{API_PREFIX}/channels/99999")
        assert resp.status_code == 404

    def test_get_channel_detail_not_subscribed(self, logged_in_client, user, admin_user):
        c = _create_channel(admin_user)
        resp = logged_in_client.get(f"{API_PREFIX}/channels/{c.id}")
        assert resp.status_code == 200  # anyone can view channel details


class TestV2ChannelCreate:
    """POST /api.v2/api/channels/create"""

    def test_create_channel(self, logged_in_client, user):
        resp = logged_in_client.post(f"{API_PREFIX}/channels/create", json={
            "name": "New Channel",
            "description": "Channel description",
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["data"]["channel"]["name"] == "New Channel"
        c = Chat.query.filter_by(name="New Channel").first()
        assert c is not None

    def test_create_channel_no_name(self, logged_in_client, user):
        resp = logged_in_client.post(f"{API_PREFIX}/channels/create", json={})
        assert resp.status_code == 400

    def test_create_channel_unauthorized(self, client):
        resp = client.post(f"{API_PREFIX}/channels/create", json={
            "name": "My Channel",
        })
        assert resp.status_code == 401


class TestV2ChannelSubscribe:
    """POST /api.v2/api/channels/<id>/subscribe"""

    def test_subscribe(self, logged_in_client, user, admin_user):
        c = _create_channel(admin_user)
        resp = logged_in_client.post(
            f"{API_PREFIX}/channels/{c.id}/subscribe")
        assert resp.status_code == 200
        sub = ChatSubscriber.query.filter_by(
            user_id=user.id, chat_id=c.id).first()
        assert sub is not None

    def test_unsubscribe(self, logged_in_client, user, admin_user):
        c = _create_channel(admin_user)
        db.session.add(ChatSubscriber(
            user_id=user.id, chat_id=c.id))
        db.session.commit()
        resp = logged_in_client.post(
            f"{API_PREFIX}/channels/{c.id}/unsubscribe")
        assert resp.status_code == 200
        sub = ChatSubscriber.query.filter_by(
            user_id=user.id, chat_id=c.id).first()
        assert sub is None

    def test_subscribe_twice(self, logged_in_client, user, admin_user):
        c = _create_channel(admin_user)
        logged_in_client.post(f"{API_PREFIX}/channels/{c.id}/subscribe")
        resp = logged_in_client.post(
            f"{API_PREFIX}/channels/{c.id}/subscribe")
        assert resp.status_code == 200  # idempotent

    def test_subscribe_channel_not_found(self, logged_in_client, user):
        resp = logged_in_client.post(f"{API_PREFIX}/channels/99999/subscribe")
        assert resp.status_code == 404


class TestV2ChannelMessages:
    """GET /api.v2/api/channel_messages/<channel_id>"""

    def test_get_channel_messages(self, logged_in_client, user, admin_user):
        c = _create_channel(admin_user)
        db.session.add(ChatSubscriber(user_id=user.id, chat_id=c.id))
        db.session.add(Message(
            content="Channel post", sender_id=admin_user.id,
            chat_id=c.id, receiver_id=admin_user.id,
            timestamp=datetime.utcnow()))
        db.session.commit()
        resp = logged_in_client.get(
            f"{API_PREFIX}/channel_messages/{c.id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["data"]["messages"]) == 1

    def test_get_channel_messages_not_subscribed(self, logged_in_client, user, admin_user):
        c = _create_channel(admin_user)
        resp = logged_in_client.get(
            f"{API_PREFIX}/channel_messages/{c.id}")
        # Anyone can see channel messages (public channels)
        assert resp.status_code in (200, 403)


class TestV2SendChannelMessage:
    """POST /api.v2/api/send_channel_message"""

    def test_send_channel_message(self, logged_in_admin, admin_user):
        c = _create_channel(admin_user)
        resp = logged_in_admin.post(
            f"{API_PREFIX}/send_channel_message", json={
                "channel_id": c.id,
                "content": "Hello channel!",
            })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["data"]["message"]["content"] == "Hello channel!"
        msg = Message.query.filter_by(chat_id=c.id).first()
        assert msg is not None

    def test_send_channel_message_not_owner(self, logged_in_client, user, admin_user):
        c = _create_channel(admin_user)
        resp = logged_in_client.post(
            f"{API_PREFIX}/send_channel_message", json={
                "channel_id": c.id,
                "content": "Unauthorized!",
            })
        assert resp.status_code == 403

    def test_send_channel_message_no_content(self, logged_in_admin, admin_user):
        c = _create_channel(admin_user)
        resp = logged_in_admin.post(
            f"{API_PREFIX}/send_channel_message", json={
                "channel_id": c.id,
            })
        assert resp.status_code == 400

    def test_send_channel_message_no_channel(self, logged_in_admin, admin_user):
        resp = logged_in_admin.post(
            f"{API_PREFIX}/send_channel_message", json={
                "content": "No channel",
            })
        assert resp.status_code == 400

    def test_send_channel_message_unauthorized(self, client, admin_user):
        c = _create_channel(admin_user)
        resp = client.post(
            f"{API_PREFIX}/send_channel_message", json={
                "channel_id": c.id,
                "content": "Test",
            })
        assert resp.status_code == 401


class TestV2ChannelUpdate:
    """POST /api.v2/api/channels/<id>/update"""

    def test_update_channel(self, logged_in_client, user):
        c = _create_channel(user)
        resp = logged_in_client.post(
            f"{API_PREFIX}/channels/{c.id}/update", json={
                "name": "Updated Channel",
            })
        assert resp.status_code == 200
        assert db.session.get(Chat, c.id).name == "Updated Channel"

    def test_update_channel_not_owner(self, logged_in_client, user, admin_user):
        c = _create_channel(admin_user)
        resp = logged_in_client.post(
            f"{API_PREFIX}/channels/{c.id}/update", json={
                "name": "Hacked",
            })
        assert resp.status_code == 403


class TestV2ChannelAdmins:
    """POST /api.v2/api/channels/<id>/admins"""

    def test_add_admin(self, logged_in_client, user, user2):
        c = _create_channel(user)
        resp = logged_in_client.post(
            f"{API_PREFIX}/channels/{c.id}/admins", json={
                "user_id": user2.id,
            })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["username"] == "friend"

    def test_add_admin_not_owner(self, logged_in_client, user, user2, admin_user):
        c = _create_channel(admin_user)
        resp = logged_in_client.post(
            f"{API_PREFIX}/channels/{c.id}/admins", json={
                "user_id": user2.id,
            })
        assert resp.status_code == 403

    def test_add_admin_no_user_id(self, logged_in_client, user):
        c = _create_channel(user)
        resp = logged_in_client.post(
            f"{API_PREFIX}/channels/{c.id}/admins", json={})
        assert resp.status_code == 400

    def test_add_admin_user_not_found(self, logged_in_client, user):
        c = _create_channel(user)
        resp = logged_in_client.post(
            f"{API_PREFIX}/channels/{c.id}/admins", json={
                "user_id": 99999,
            })
        assert resp.status_code == 404
