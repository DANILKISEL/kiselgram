"""Tests for V2 API saved messages under /api.v2/api/."""

from datetime import datetime
from app import db
from app.models import Message


API_PREFIX = "/api.v2/api"


class TestV2SavedMessages:
    """GET/POST /api.v2/api/saved_messages"""

    def test_get_saved_empty(self, logged_in_client, user):
        resp = logged_in_client.get(f"{API_PREFIX}/saved_messages")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["messages"] == []

    def test_save_message(self, logged_in_client, user, user2):
        msg = Message(content="Save me!", sender_id=user2.id,
                      receiver_id=user.id, timestamp=datetime.utcnow())
        db.session.add(msg)
        db.session.commit()
        resp = logged_in_client.post(f"{API_PREFIX}/saved_messages", json={
            "message_id": msg.id,
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["success"] is True
        assert db.session.get(Message, msg.id).is_saved is True

    def test_save_message_already_saved(self, logged_in_client, user, user2):
        msg = Message(content="Already saved", sender_id=user2.id,
                      receiver_id=user.id, is_saved=True,
                      timestamp=datetime.utcnow())
        db.session.add(msg)
        db.session.commit()
        resp = logged_in_client.post(f"{API_PREFIX}/saved_messages", json={
            "message_id": msg.id,
        })
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "ALREADY_SAVED"

    def test_save_message_not_found(self, logged_in_client, user):
        resp = logged_in_client.post(f"{API_PREFIX}/saved_messages", json={
            "message_id": 99999,
        })
        assert resp.status_code == 404

    def test_save_message_missing_id(self, logged_in_client, user):
        resp = logged_in_client.post(f"{API_PREFIX}/saved_messages", json={})
        assert resp.status_code == 400

    def test_get_saved_with_data(self, logged_in_client, user, user2):
        msg = Message(content="Saved item", sender_id=user2.id,
                      receiver_id=user.id, is_saved=True,
                      timestamp=datetime.utcnow())
        db.session.add(msg)
        db.session.commit()
        resp = logged_in_client.get(f"{API_PREFIX}/saved_messages")
        data = resp.get_json()
        assert len(data["data"]["messages"]) == 1
        assert data["data"]["messages"][0]["original_message"]["content"] == "Saved item"

    def test_saved_messages_unauthorized(self, client):
        resp = client.get(f"{API_PREFIX}/saved_messages")
        assert resp.status_code == 401


class TestV2SavedNote:
    """POST /api.v2/api/saved_messages/<saved_id>/note"""

    def test_update_saved_note(self, logged_in_client, user, user2):
        msg = Message(content="With note", sender_id=user2.id,
                      receiver_id=user.id, is_saved=True,
                      timestamp=datetime.utcnow())
        db.session.add(msg)
        db.session.commit()
        resp = logged_in_client.post(
            f"{API_PREFIX}/saved_messages/{msg.id}/note", json={
                "note": "My important note",
            })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["note"] == "My important note"
