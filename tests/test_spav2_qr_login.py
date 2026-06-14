"""Tests for V2/V3 QR login endpoints under /api.v2/api/auth/qr/*."""

from datetime import datetime, timedelta, timezone
import secrets
from app import db
from app.models import User, QrLoginToken


API_PREFIX = "/api.v2/api"


class TestV2QrGenerate:
    """POST /api.v2/api/auth/qr/generate — Mode A (logged-in device generates QR)"""

    def test_generate_qr(self, logged_in_client, user):
        resp = logged_in_client.post(f"{API_PREFIX}/auth/qr/generate")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "token" in data["data"]
        assert data["data"]["expires_in"] == 120
        qr = QrLoginToken.query.filter_by(token=data["data"]["token"]).first()
        assert qr is not None
        assert qr.user_id == user.id

    def test_generate_qr_unauthorized(self, client):
        resp = client.post(f"{API_PREFIX}/auth/qr/generate")
        assert resp.status_code == 401


class TestV2QrRequest:
    """POST /api.v2/api/auth/qr/request — Mode B (unauthenticated requests QR)"""

    def test_request_qr(self, client):
        resp = client.post(f"{API_PREFIX}/auth/qr/request")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "token" in data["data"]
        qr = QrLoginToken.query.filter_by(token=data["data"]["token"]).first()
        assert qr is not None
        assert qr.user_id is None  # unclaimed


class TestV2QrAuthorize:
    """POST /api.v2/api/auth/qr/authorize — Mode B (logged-in device authorizes)"""

    def test_authorize_qr(self, logged_in_client, user, client):
        # Create unclaimed QR token
        token = secrets.token_urlsafe(32)
        qr = QrLoginToken(
            token=token,
            user_id=None,
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=2),
        )
        db.session.add(qr)
        db.session.commit()
        resp = logged_in_client.post(f"{API_PREFIX}/auth/qr/authorize", json={
            "token": token,
        })
        assert resp.status_code == 200
        assert db.session.get(QrLoginToken, qr.id).user_id == user.id

    def test_authorize_qr_invalid(self, logged_in_client, user):
        resp = logged_in_client.post(f"{API_PREFIX}/auth/qr/authorize", json={
            "token": "nonexistent_token",
        })
        assert resp.status_code == 400

    def test_authorize_qr_missing_token(self, logged_in_client, user):
        resp = logged_in_client.post(f"{API_PREFIX}/auth/qr/authorize", json={})
        assert resp.status_code == 400

    def test_authorize_qr_unauthorized(self, client):
        resp = client.post(f"{API_PREFIX}/auth/qr/authorize", json={
            "token": "sometoken",
        })
        assert resp.status_code == 401


class TestV2QrLogin:
    """POST /api.v2/api/auth/qr/login — finalize login"""

    def test_qr_login(self, logged_in_client, user, client):
        # Create an authorized QR token
        token = secrets.token_urlsafe(32)
        qr = QrLoginToken(
            token=token,
            user_id=user.id,
            authorized_by_id=user.id,
            consumed=False,
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=2),
        )
        db.session.add(qr)
        db.session.commit()
        resp = client.post(f"{API_PREFIX}/auth/qr/login", json={
            "token": token,
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["user"]["username"] == "testuser"
        assert "session_token" in data["data"]
        # Token should be consumed
        assert db.session.get(QrLoginToken, qr.id).consumed is True

    def test_qr_login_not_authorized(self, client):
        token = secrets.token_urlsafe(32)
        qr = QrLoginToken(
            token=token,
            user_id=None,
            consumed=False,
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=2),
        )
        db.session.add(qr)
        db.session.commit()
        resp = client.post(f"{API_PREFIX}/auth/qr/login", json={
            "token": token,
        })
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "NOT_AUTHORIZED"

    def test_qr_login_invalid_token(self, client):
        resp = client.post(f"{API_PREFIX}/auth/qr/login", json={
            "token": "bad_token",
        })
        assert resp.status_code == 400


class TestV2QrStatus:
    """GET /api.v2/api/auth/qr/status/<token>"""

    def test_qr_status(self, logged_in_client, user, client):
        token = secrets.token_urlsafe(32)
        qr = QrLoginToken(
            token=token,
            user_id=user.id,
            consumed=False,
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=2),
        )
        db.session.add(qr)
        db.session.commit()
        resp = client.get(f"{API_PREFIX}/auth/qr/status/{token}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["consumed"] is False
        assert data["data"]["authorized"] is True

    def test_qr_status_not_found(self, client):
        resp = client.get(f"{API_PREFIX}/auth/qr/status/nonexistent")
        assert resp.status_code == 404
