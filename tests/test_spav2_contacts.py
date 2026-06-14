"""Tests for V2 API contact/block endpoints under /api.v2/api/."""

from datetime import datetime
from app import db
from app.models import User, Contact, BlockedUser


API_PREFIX = "/api.v2/api"


class TestV2Contacts:
    """GET/POST /api.v2/api/contacts, rename, delete"""

    def test_get_contacts_empty(self, logged_in_client, user):
        resp = logged_in_client.get(f"{API_PREFIX}/contacts")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["contacts"] == []

    def test_add_contact(self, logged_in_client, user, user2):
        resp = logged_in_client.post(f"{API_PREFIX}/contacts", json={
            "contact_id": user2.id,
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["success"] is True
        c = Contact.query.filter_by(user_id=user.id, contact_id=user2.id).first()
        assert c is not None

    def test_add_contact_duplicate(self, logged_in_client, user, user2):
        db.session.add(Contact(user_id=user.id, contact_id=user2.id))
        db.session.commit()
        resp = logged_in_client.post(f"{API_PREFIX}/contacts", json={
            "contact_id": user2.id,
        })
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "ALREADY_CONTACT"

    def test_add_contact_nonexistent(self, logged_in_client, user):
        resp = logged_in_client.post(f"{API_PREFIX}/contacts", json={
            "contact_id": 99999,
        })
        assert resp.status_code == 404

    def test_add_contact_missing_id(self, logged_in_client, user):
        resp = logged_in_client.post(f"{API_PREFIX}/contacts", json={})
        assert resp.status_code == 400

    def test_rename_contact(self, logged_in_client, user, user2):
        db.session.add(Contact(user_id=user.id, contact_id=user2.id))
        db.session.commit()
        resp = logged_in_client.post(f"{API_PREFIX}/contacts/rename", json={
            "contact_id": user2.id,
            "name": "Best Friend",
        })
        assert resp.status_code == 200
        c = Contact.query.filter_by(user_id=user.id, contact_id=user2.id).first()
        assert c.custom_name == "Best Friend"

    def test_rename_contact_not_found(self, logged_in_client, user, user2):
        resp = logged_in_client.post(f"{API_PREFIX}/contacts/rename", json={
            "contact_id": user2.id,
            "name": "Stranger",
        })
        assert resp.status_code == 404

    def test_remove_contact(self, logged_in_client, user, user2):
        db.session.add(Contact(user_id=user.id, contact_id=user2.id))
        db.session.commit()
        resp = logged_in_client.delete(
            f"{API_PREFIX}/contacts/{user2.id}")
        assert resp.status_code == 200
        c = Contact.query.filter_by(user_id=user.id, contact_id=user2.id).first()
        assert c is None

    def test_remove_contact_not_exists(self, logged_in_client, user, user2):
        resp = logged_in_client.delete(
            f"{API_PREFIX}/contacts/{user2.id}")
        assert resp.status_code == 200  # idempotent

    def test_contacts_unauthorized(self, client):
        resp = client.get(f"{API_PREFIX}/contacts")
        assert resp.status_code == 401


class TestV2BlockUnblock:
    """POST /api.v2/api/block_user/<id>, /api.v2/api/unblock_user/<id>, GET /api.v2/api/blocked_users"""

    def test_block_user(self, logged_in_client, user, user2):
        resp = logged_in_client.post(f"{API_PREFIX}/block_user/{user2.id}")
        assert resp.status_code == 200
        block = BlockedUser.query.filter_by(
            user_id=user.id, blocked_user_id=user2.id).first()
        assert block is not None

    def test_block_user_already_blocked(self, logged_in_client, user, user2):
        db.session.add(BlockedUser(user_id=user.id, blocked_user_id=user2.id))
        db.session.commit()
        resp = logged_in_client.post(f"{API_PREFIX}/block_user/{user2.id}")
        assert resp.status_code == 200  # idempotent - still succeeds

    def test_unblock_user(self, logged_in_client, user, user2):
        db.session.add(BlockedUser(user_id=user.id, blocked_user_id=user2.id))
        db.session.commit()
        resp = logged_in_client.post(f"{API_PREFIX}/unblock_user/{user2.id}")
        assert resp.status_code == 200
        block = BlockedUser.query.filter_by(
            user_id=user.id, blocked_user_id=user2.id).first()
        assert block is None

    def test_get_blocked_users(self, logged_in_client, user, user2):
        db.session.add(BlockedUser(user_id=user.id, blocked_user_id=user2.id))
        db.session.commit()
        resp = logged_in_client.get(f"{API_PREFIX}/blocked_users")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["data"]["blocked_users"]) == 1
        assert data["data"]["blocked_users"][0]["user_id"] == user2.id

    def test_get_blocked_users_empty(self, logged_in_client, user):
        resp = logged_in_client.get(f"{API_PREFIX}/blocked_users")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["blocked_users"] == []

    def test_block_unauthorized(self, client, user2):
        resp = client.post(f"{API_PREFIX}/block_user/{user2.id}")
        assert resp.status_code == 401
