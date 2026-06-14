"""Tests for V2 API sessions endpoints under /api.v2/api/."""

from datetime import datetime
from app import db
from app.models import UserSession


API_PREFIX = "/api.v2/api"


class TestV2Sessions:
    """GET/DELETE /api.v2/api/sessions"""

    def test_list_sessions(self, logged_in_client, user):
        # Create a few sessions
        for i in range(3):
            db.session.add(UserSession(
                user_id=user.id,
                session_token=f"token_{i}",
                device=f"Device {i}",
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                is_active=True,
            ))
        db.session.commit()
        resp = logged_in_client.get(f"{API_PREFIX}/sessions")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["data"]["sessions"]) == 3

    def test_list_sessions_empty(self, logged_in_client, user):
        resp = logged_in_client.get(f"{API_PREFIX}/sessions")
        data = resp.get_json()
        assert data["data"]["sessions"] == []

    def test_list_sessions_unauthorized(self, client):
        resp = client.get(f"{API_PREFIX}/sessions")
        assert resp.status_code == 401

    def test_terminate_session(self, logged_in_client, user):
        s = UserSession(
            user_id=user.id, session_token="term_token",
            device="Old Device", created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(), is_active=True)
        db.session.add(s)
        db.session.commit()
        resp = logged_in_client.delete(f"{API_PREFIX}/sessions/{s.id}")
        assert resp.status_code == 200
        assert db.session.get(UserSession, s.id).is_active is False

    def test_terminate_session_not_own(self, logged_in_client, user, user2):
        s = UserSession(
            user_id=user2.id, session_token="other_token",
            device="Other", created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(), is_active=True)
        db.session.add(s)
        db.session.commit()
        resp = logged_in_client.delete(f"{API_PREFIX}/sessions/{s.id}")
        assert resp.status_code == 404

    def test_terminate_session_not_found(self, logged_in_client, user):
        resp = logged_in_client.delete(f"{API_PREFIX}/sessions/99999")
        assert resp.status_code == 404
