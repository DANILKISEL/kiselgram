"""Tests for V2 API auth endpoints under /api.v2/api/auth/* and related."""

from datetime import datetime, timedelta
import secrets
from app import db
from app.models import User, EmailVerification, UserSession


API_PREFIX = "/api.v2/api"


class TestV2Register:
    """POST /api.v2/api/auth/register"""

    def test_register_success(self, client, session):
        resp = client.post(f"{API_PREFIX}/auth/register", json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "StrongPass1!",
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["success"] is True
        user_data = data["data"]["user"]
        assert user_data["username"] == "newuser"
        assert user_data["email"] == "new@example.com"
        assert "verification_token" in data["data"]
        user = User.query.filter_by(username="newuser").first()
        assert user is not None
        assert user.email_verified is False

    def test_register_duplicate_username(self, client, session, user):
        resp = client.post(f"{API_PREFIX}/auth/register", json={
            "username": "testuser",
            "email": "other@example.com",
            "password": "StrongPass1!",
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
        assert "username" in data["error"]["fields"]

    def test_register_duplicate_email(self, client, session, user):
        resp = client.post(f"{API_PREFIX}/auth/register", json={
            "username": "anotheruser",
            "email": "test@example.com",
            "password": "StrongPass1!",
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
        assert "email" in data["error"]["fields"]

    def test_register_short_username(self, client, session):
        resp = client.post(f"{API_PREFIX}/auth/register", json={
            "username": "ab",
            "email": "ab@example.com",
            "password": "StrongPass1!",
        })
        assert resp.status_code == 400
        assert "username" in resp.get_json()["error"]["fields"]

    def test_register_invalid_email(self, client, session):
        resp = client.post(f"{API_PREFIX}/auth/register", json={
            "username": "validuser",
            "email": "notanemail",
            "password": "StrongPass1!",
        })
        assert resp.status_code == 400
        assert "email" in resp.get_json()["error"]["fields"]

    def test_register_weak_password(self, client, session):
        resp = client.post(f"{API_PREFIX}/auth/register", json={
            "username": "weakpassuser",
            "email": "weak@example.com",
            "password": "short",
        })
        assert resp.status_code == 400
        assert "password" in resp.get_json()["error"]["fields"]


class TestV2Login:
    """POST /api.v2/api/auth/login"""

    def test_login_success(self, client, session, user):
        resp = client.post(f"{API_PREFIX}/auth/login", json={
            "username": "testuser",
            "password": "testpass",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["user"]["username"] == "testuser"
        assert "session_token" in data["data"]
        # Verify UserSession was created
        session_token = data["data"]["session_token"]
        us = UserSession.query.filter_by(session_token=session_token).first()
        assert us is not None
        assert us.user_id == user.id

    def test_login_wrong_password(self, client, session, user):
        resp = client.post(f"{API_PREFIX}/auth/login", json={
            "username": "testuser",
            "password": "wrongpass",
        })
        assert resp.status_code == 401
        data = resp.get_json()

    def test_login_nonexistent_user(self, client, session):
        resp = client.post(f"{API_PREFIX}/auth/login", json={
            "username": "nobody",
            "password": "anypass",
        })
        assert resp.status_code == 401

    def test_login_unverified_email(self, client, session):
        u = User(username="unverified", email="unverified@example.com",
                 email_verified=False)
        u.set_password("testpass")
        db.session.add(u)
        db.session.commit()
        resp = client.post(f"{API_PREFIX}/auth/login", json={
            "username": "unverified",
            "password": "testpass",
        })
        assert resp.status_code == 403
        data = resp.get_json()
        assert data["error"]["code"] == "EMAIL_NOT_VERIFIED"

    def test_login_missing_fields(self, client, session):
        resp = client.post(f"{API_PREFIX}/auth/login", json={
            "username": "",
            "password": "",
        })
        assert resp.status_code == 401


class TestV2Logout:
    """POST /api.v2/api/auth/logout"""

    def test_logout_logged_in(self, logged_in_client, user):
        resp = logged_in_client.post(f"{API_PREFIX}/auth/logout")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_logout_no_session(self, client):
        resp = client.post(f"{API_PREFIX}/auth/logout")
        assert resp.status_code == 200  # still succeeds even if not logged in


class TestV2VerifyEmail:
    """GET/POST /api.v2/api/auth/verify"""

    def test_verify_email_success(self, client, session):
        u = User(username="verifyuser", email="verify@example.com",
                 email_verified=False)
        u.set_password("testpass")
        db.session.add(u)
        db.session.flush()
        token = secrets.token_urlsafe(32)
        db.session.add(EmailVerification(
            user_id=u.id, token=token,
            expires_at=datetime.utcnow() + timedelta(hours=24)))
        db.session.commit()

        resp = client.get(f"{API_PREFIX}/auth/verify?token={token}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert db.session.get(User, u.id).email_verified is True

    def test_verify_email_post(self, client, session):
        u = User(username="verifypost", email="verifypost@example.com",
                 email_verified=False)
        u.set_password("testpass")
        db.session.add(u)
        db.session.flush()
        token = secrets.token_urlsafe(32)
        db.session.add(EmailVerification(
            user_id=u.id, token=token,
            expires_at=datetime.utcnow() + timedelta(hours=24)))
        db.session.commit()

        resp = client.post(f"{API_PREFIX}/auth/verify", json={"token": token})
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_verify_email_invalid_token(self, client, session):
        resp = client.get(f"{API_PREFIX}/auth/verify?token=invalidtoken123")
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False

    def test_verify_email_missing_token(self, client, session):
        resp = client.get(f"{API_PREFIX}/auth/verify")
        assert resp.status_code == 400

    def test_verify_email_expired_token(self, client, session):
        u = User(username="expireduser", email="expired@example.com",
                 email_verified=False)
        u.set_password("testpass")
        db.session.add(u)
        db.session.flush()
        token = secrets.token_urlsafe(32)
        db.session.add(EmailVerification(
            user_id=u.id, token=token,
            expires_at=datetime.utcnow() - timedelta(hours=1)))
        db.session.commit()

        resp = client.get(f"{API_PREFIX}/auth/verify?token={token}")
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "EXPIRED_TOKEN"


class TestV2CheckUsername:
    """GET /api.v2/api/auth/check_username"""

    def test_check_username_available(self, client, session):
        resp = client.get(f"{API_PREFIX}/auth/check_username?username=newuser")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["available"] is True

    def test_check_username_taken(self, client, session, user):
        resp = client.get(f"{API_PREFIX}/auth/check_username?username=testuser")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["available"] is False or data["data"]["available"] is None

    def test_check_username_missing(self, client, session):
        resp = client.get(f"{API_PREFIX}/auth/check_username")
        assert resp.status_code == 400
