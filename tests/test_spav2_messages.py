"""Tests for V2 API message endpoints under /api.v2/api/...

Covers send_message, mark_read, edit, delete, reactions, typing.
"""

from datetime import datetime
from app import db
from app.models import Message, Reaction, Reply, User


API_PREFIX = "/api.v2/api"


class TestV2SendMessage:
    """POST /api.v2/api/send_message"""

    def test_send_personal_message(self, logged_in_client, user, user2):
        resp = logged_in_client.post(f"{API_PREFIX}/send_message", json={
            "receiver_id": user2.id,
            "content": "Hello from V2!",
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["success"] is True
        msg_data = data["data"]["message"]
        assert msg_data["content"] == "Hello from V2!"
        assert msg_data["sender_id"] == user.id
        assert msg_data["receiver_id"] == user2.id

    def test_send_message_with_reply(self, logged_in_client, user, user2):
        original = Message(content="Original", sender_id=user.id,
                           receiver_id=user2.id, timestamp=datetime.utcnow())
        db.session.add(original)
        db.session.commit()
        resp = logged_in_client.post(f"{API_PREFIX}/send_message", json={
            "receiver_id": user2.id,
            "content": "This is a reply",
            "reply_to_id": original.id,
        })
        assert resp.status_code == 201
        reply = Reply.query.filter_by(original_message_id=original.id).first()
        assert reply is not None

    def test_send_message_no_content(self, logged_in_client, user, user2):
        resp = logged_in_client.post(f"{API_PREFIX}/send_message", json={
            "receiver_id": user2.id,
            "content": "",
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["error"]["code"] == "VALIDATION_ERROR"

    def test_send_message_no_receiver(self, logged_in_client, user):
        resp = logged_in_client.post(f"{API_PREFIX}/send_message", json={
            "content": "Missing receiver",
        })
        assert resp.status_code == 400

    def test_send_message_unauthorized(self, client, user2):
        resp = client.post(f"{API_PREFIX}/send_message", json={
            "receiver_id": user2.id,
            "content": "No auth",
        })
        assert resp.status_code == 401

    def test_send_message_blocked(self, logged_in_client, user, user2):
        from app.models import BlockedUser
        db.session.add(BlockedUser(user_id=user2.id, blocked_user_id=user.id))
        db.session.commit()
        resp = logged_in_client.post(f"{API_PREFIX}/send_message", json={
            "receiver_id": user2.id,
            "content": "You blocked me?",
        })
        assert resp.status_code == 403
        assert resp.get_json()["error"]["code"] == "USER_BLOCKED"


class TestV2MarkRead:
    """POST /api.v2/api/mark_read/<user_id>"""

    def test_mark_read_success(self, logged_in_client, user, user2):
        msg = Message(content="Unread msg", sender_id=user2.id,
                      receiver_id=user.id, is_read=False,
                      timestamp=datetime.utcnow())
        db.session.add(msg)
        db.session.commit()
        resp = logged_in_client.post(f"{API_PREFIX}/mark_read/{user2.id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["marked_count"] >= 1
        updated = db.session.get(Message, msg.id)
        assert updated.is_read is True

    def test_mark_read_unauthorized(self, client, user2):
        resp = client.post(f"{API_PREFIX}/mark_read/{user2.id}")
        assert resp.status_code == 401


class TestV2EditMessage:
    """POST /api.v2/api/messages/<message_id>/edit"""

    def test_edit_own_message(self, logged_in_client, user, user2):
        msg = Message(content="Original text", sender_id=user.id,
                      receiver_id=user2.id, timestamp=datetime.utcnow())
        db.session.add(msg)
        db.session.commit()
        resp = logged_in_client.post(
            f"{API_PREFIX}/messages/{msg.id}/edit", json={"content": "Edited text"})
        assert resp.status_code == 200
        assert resp.get_json()["data"]["message"]["content"] == "Edited text"
        assert db.session.get(Message, msg.id).edited_at is not None

    def test_edit_others_message(self, logged_in_client, user, user2):
        msg = Message(content="Not yours", sender_id=user2.id,
                      receiver_id=user.id, timestamp=datetime.utcnow())
        db.session.add(msg)
        db.session.commit()
        resp = logged_in_client.post(
            f"{API_PREFIX}/messages/{msg.id}/edit", json={"content": "Hacked!"})
        assert resp.status_code == 403
        assert resp.get_json()["error"]["code"] == "FORBIDDEN"

    def test_edit_empty_content(self, logged_in_client, user, user2):
        msg = Message(content="Some text", sender_id=user.id,
                      receiver_id=user2.id, timestamp=datetime.utcnow())
        db.session.add(msg)
        db.session.commit()
        resp = logged_in_client.post(
            f"{API_PREFIX}/messages/{msg.id}/edit", json={"content": ""})
        assert resp.status_code == 400

    def test_edit_nonexistent_message(self, logged_in_client, user):
        resp = logged_in_client.post(
            f"{API_PREFIX}/messages/99999/edit", json={"content": "Nope"})
        assert resp.status_code == 404


class TestV2DeleteMessage:
    """POST /api.v2/api/messages/<message_id>/delete"""

    def test_delete_own_message(self, logged_in_client, user, user2):
        msg = Message(content="Delete me", sender_id=user.id,
                      receiver_id=user2.id, timestamp=datetime.utcnow())
        db.session.add(msg)
        db.session.commit()
        resp = logged_in_client.post(f"{API_PREFIX}/messages/{msg.id}/delete")
        assert resp.status_code == 200
        assert db.session.get(Message, msg.id).is_deleted is True

    def test_delete_others_message(self, logged_in_client, user, user2):
        msg = Message(content="Not yours", sender_id=user2.id,
                      receiver_id=user.id, timestamp=datetime.utcnow())
        db.session.add(msg)
        db.session.commit()
        resp = logged_in_client.post(f"{API_PREFIX}/messages/{msg.id}/delete")
        assert resp.status_code == 403


class TestV2Reactions:
    """POST /api.v2/api/reactions/add and GET /api.v2/api/reactions/<message_id>"""

    def test_add_reaction(self, logged_in_client, user, user2):
        msg = Message(content="React to me", sender_id=user.id,
                      receiver_id=user2.id, timestamp=datetime.utcnow())
        db.session.add(msg)
        db.session.commit()
        resp = logged_in_client.post(f"{API_PREFIX}/reactions/add", json={
            "message_id": msg.id,
            "reaction_type": "+1",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["has_reacted"] is True
        assert data["data"]["reaction_count"] == 1

    def test_remove_reaction(self, logged_in_client, user, user2):
        msg = Message(content="Toggle reaction", sender_id=user.id,
                      receiver_id=user2.id, timestamp=datetime.utcnow())
        db.session.add(msg)
        db.session.commit()
        resp = logged_in_client.post(f"{API_PREFIX}/reactions/add", json={
            "message_id": msg.id,
            "reaction_type": "+1",
        })
        assert resp.get_json()["data"]["has_reacted"] is True
        # Toggle off
        resp2 = logged_in_client.post(f"{API_PREFIX}/reactions/add", json={
            "message_id": msg.id,
            "reaction_type": "+1",
        })
        assert resp2.get_json()["data"]["has_reacted"] is False

    def test_get_reactions(self, logged_in_client, user, user2):
        msg = Message(content="Check reactions", sender_id=user.id,
                      receiver_id=user2.id, timestamp=datetime.utcnow())
        db.session.add(msg)
        db.session.commit()
        db.session.add(Reaction(message_id=msg.id, user_id=user.id,
                                reaction_type="heart"))
        db.session.commit()
        resp = logged_in_client.get(f"{API_PREFIX}/reactions/{msg.id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["data"]["reactions"]) == 1
        assert data["data"]["reactions"][0]["reaction_type"] == "heart"

    def test_reaction_missing_type(self, logged_in_client, user, user2):
        msg = Message(content="No reaction type", sender_id=user.id,
                      receiver_id=user2.id, timestamp=datetime.utcnow())
        db.session.add(msg)
        db.session.commit()
        resp = logged_in_client.post(f"{API_PREFIX}/reactions/add", json={
            "message_id": msg.id,
        })
        assert resp.status_code == 400


class TestV2Typing:
    """POST /api.v2/api/typing/<chat_type>/<chat_id>"""

    def test_set_typing_personal(self, logged_in_client, user, user2):
        resp = logged_in_client.post(
            f"{API_PREFIX}/typing/personal/{user2.id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["is_typing"] is True

    def test_set_typing_unauthorized(self, client, user2):
        resp = client.post(f"{API_PREFIX}/typing/personal/{user2.id}")
        assert resp.status_code == 401
