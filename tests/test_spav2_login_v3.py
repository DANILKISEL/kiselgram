"""Tests for V3 multi-step login endpoints under /api.v2/api/auth/*."""

from datetime import datetime, timedelta, timezone
import secrets
from app import db
from app.models import User, LoginOtp, EmailVerification


API_PREFIX = "/api.v2/api"


class TestV3CheckEmail:
    """POST /api.v2/api/auth/check-email"""

    def test_check_email_exists(self, client, session, user):
        resp = client.post(f"{API_PREFIX}/auth/check-email", json={
            "email": "test@example.com",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["exists"] is True

    def test_check_email_not_exists(self, client, session):
        resp = client.post(f"{API_PREFIX}/auth/check-email", json={
            "email": "nobody@example.com",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["exists"] is False

    def test_check_email_invalid(self, client, session):
        resp = client.post(f"{API_PREFIX}/auth/check-email", json={
            "email": "",
        })
        assert resp.status_code == 400


class TestV3SendOtp:
    """POST /api.v2/api/auth/send-otp"""

    def test_send_otp(self, client, session, user):
        resp = client.post(f"{API_PREFIX}/auth/send-otp", json={
            "email": "test@example.com",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        otp = LoginOtp.query.filter_by(user_id=user.id).first()
        assert otp is not None
        assert otp.used is False

    def test_send_otp_user_not_found(self, client, session):
        resp = client.post(f"{API_PREFIX}/auth/send-otp", json={
            "email": "unknown@example.com",
        })
        assert resp.status_code == 404


class TestV3VerifyOtp:
    """POST /api.v2/api/auth/verify-otp"""

    def test_verify_otp(self, client, session, user):
        code = "123456"
        otp = LoginOtp(user_id=user.id, code=code, used=False,
                       expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=5))
        db.session.add(otp)
        db.session.commit()
        resp = client.post(f"{API_PREFIX}/auth/verify-otp", json={
            "email": "test@example.com",
            "code": code,
        })
        assert resp.status_code == 200
        assert db.session.get(LoginOtp, otp.id).used is True

    def test_verify_otp_invalid_code(self, client, session, user):
        resp = client.post(f"{API_PREFIX}/auth/verify-otp", json={
            "email": "test@example.com",
            "code": "000000",
        })
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "INVALID_CODE"

    def test_verify_otp_expired(self, client, session, user):
        code = "654321"
        otp = LoginOtp(user_id=user.id, code=code, used=False,
                       expires_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1))
        db.session.add(otp)
        db.session.commit()
        resp = client.post(f"{API_PREFIX}/auth/verify-otp", json={
            "email": "test@example.com",
            "code": code,
        })
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "EXPIRED_CODE"

    def test_verify_otp_user_not_found(self, client, session):
        resp = client.post(f"{API_PREFIX}/auth/verify-otp", json={
            "email": "nobody@example.com",
            "code": "123456",
        })
        assert resp.status_code == 404


class TestV3LoginPassword:
    """POST /api.v2/api/auth/login-password"""

    def test_login_password(self, client, session, user):
        resp = client.post(f"{API_PREFIX}/auth/login-password", json={
            "email": "test@example.com",
            "password": "testpass",
            "otp_verified": True,
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "session_token" in data["data"]

    def test_login_password_wrong_password(self, client, session, user):
        resp = client.post(f"{API_PREFIX}/auth/login-password", json={
            "email": "test@example.com",
            "password": "wrong",
            "otp_verified": True,
        })
        assert resp.status_code == 401

    def test_login_password_no_otp(self, client, session, user):
        resp = client.post(f"{API_PREFIX}/auth/login-password", json={
            "email": "test@example.com",
            "password": "testpass",
            "otp_verified": False,
        })
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "OTP_REQUIRED"


class TestV3LoginOtpOnly:
    """POST /api.v2/api/auth/login-otp-only"""

    def test_login_otp_only(self, client, session, user):
        resp = client.post(f"{API_PREFIX}/auth/login-otp-only", json={
            "email": "test@example.com",
            "otp_verified": True,
        })
        assert resp.status_code == 200
        assert "session_token" in resp.get_json()["data"]

    def test_login_otp_only_no_otp(self, client, session, user):
        resp = client.post(f"{API_PREFIX}/auth/login-otp-only", json={
            "email": "test@example.com",
            "otp_verified": False,
        })
        assert resp.status_code == 400


class TestV3RegisterFlow:
    """POST register-send-code → register-verify-code → register-finish"""

    def test_register_send_code(self, client, session):
        resp = client.post(f"{API_PREFIX}/auth/register-send-code", json={
            "email": "newreg@example.com",
        })
        assert resp.status_code == 200
        ev = EmailVerification.query.filter_by(email="newreg@example.com").first()
        assert ev is not None
        assert ev.verified is False

    def test_register_send_code_taken(self, client, session, user):
        resp = client.post(f"{API_PREFIX}/auth/register-send-code", json={
            "email": "test@example.com",
        })
        assert resp.status_code == 409

    def test_register_verify_code(self, client, session):
        ev = EmailVerification(
            email="reg@example.com", token="abc123",
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=10),
            verified=False)
        db.session.add(ev)
        db.session.commit()
        resp = client.post(f"{API_PREFIX}/auth/register-verify-code", json={
            "email": "reg@example.com",
            "code": "abc123",
        })
        assert resp.status_code == 200
        assert db.session.get(EmailVerification, ev.id).verified is True

    def test_register_verify_code_invalid(self, client, session):
        resp = client.post(f"{API_PREFIX}/auth/register-verify-code", json={
            "email": "reg@example.com",
            "code": "wrong",
        })
        assert resp.status_code == 400

    def test_register_finish(self, client, session):
        ev = EmailVerification(
            email="finish@example.com", token="verified",
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=10),
            verified=True)
        db.session.add(ev)
        db.session.commit()
        resp = client.post(f"{API_PREFIX}/auth/register-finish", json={
            "email": "finish@example.com",
            "username": "finishuser",
            "display_name": "Finish User",
            "email_verified": True,
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["user"]["username"] == "finishuser"
        assert "session_token" in data["data"]
        user = User.query.filter_by(username="finishuser").first()
        assert user is not None

    def test_register_finish_no_verify(self, client, session):
        resp = client.post(f"{API_PREFIX}/auth/register-finish", json={
            "email": "noverify@example.com",
            "username": "noverifyuser",
            "email_verified": False,
        })
        assert resp.status_code == 400

    def test_register_finish_duplicate_username(self, client, session, user):
        resp = client.post(f"{API_PREFIX}/auth/register-finish", json={
            "email": "dup@example.com",
            "username": "testuser",
            "email_verified": True,
        })
        assert resp.status_code == 400


class TestV3PreloadedAvatars:
    """GET /api.v2/api/auth/preloaded-avatars"""

    def test_list_preloaded_avatars(self, client, session):
        resp = client.get(f"{API_PREFIX}/auth/preloaded-avatars")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "avatars" in data["data"]
