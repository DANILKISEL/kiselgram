"""Tests for V2 API profile endpoints under /api.v2/api/.

Covers GET/PUT profile, settings, privacy, avatar upload.
"""

import io
import os
import tempfile
from app import db
from app.models import User


API_PREFIX = "/api.v2/api"


class TestV2GetProfile:
    """GET /api.v2/api/profile"""

    def test_get_profile(self, logged_in_client, user):
        resp = logged_in_client.get(f"{API_PREFIX}/profile")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["username"] == "testuser"
        assert data["data"]["display_name"] == "Test User"
        assert data["data"]["user_id"] == user.id

    def test_get_profile_unauthorized(self, client):
        resp = client.get(f"{API_PREFIX}/profile")
        assert resp.status_code == 401


class TestV2UpdateProfile:
    """PUT /api.v2/api/profile"""

    def test_update_display_name(self, logged_in_client, user):
        resp = logged_in_client.put(f"{API_PREFIX}/profile", json={
            "display_name": "Updated Name",
        })
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True
        assert db.session.get(User, user.id).display_name == "Updated Name"

    def test_update_bio(self, logged_in_client, user):
        resp = logged_in_client.put(f"{API_PREFIX}/profile", json={
            "bio": "This is my new bio!",
        })
        assert resp.status_code == 200
        assert db.session.get(User, user.id).bio == "This is my new bio!"

    def test_update_status_emoji(self, logged_in_client, user):
        resp = logged_in_client.put(f"{API_PREFIX}/profile", json={
            "status_emoji": "🎉",
        })
        assert resp.status_code == 200
        assert db.session.get(User, user.id).status_emoji == "🎉"

    def test_update_profile_unauthorized(self, client):
        resp = client.put(f"{API_PREFIX}/profile", json={
            "display_name": "Hacker",
        })
        assert resp.status_code == 401


class TestV2Settings:
    """GET /api.v2/api/profile/settings"""

    def test_get_settings(self, logged_in_client, user):
        resp = logged_in_client.get(f"{API_PREFIX}/profile/settings")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "theme" in data["data"]
        assert "font_size" in data["data"]
        assert "colors" in data["data"]

    def test_get_settings_unauthorized(self, client):
        resp = client.get(f"{API_PREFIX}/profile/settings")
        assert resp.status_code == 401


class TestV2Privacy:
    """GET /api.v2/api/profile/privacy"""

    def test_get_privacy(self, logged_in_client, user):
        resp = logged_in_client.get(f"{API_PREFIX}/profile/privacy")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "last_seen" in data["data"]
        assert "profile_photo" in data["data"]
        assert "calls" in data["data"]
        assert "messages" in data["data"]

    def test_get_privacy_unauthorized(self, client):
        resp = client.get(f"{API_PREFIX}/profile/privacy")
        assert resp.status_code == 401


class TestV2UploadAvatar:
    """POST /api.v2/api/profile/avatar"""

    def test_upload_avatar(self, logged_in_client, user):
        data = {
            "avatar": (io.BytesIO(b"fake-png-data"), "avatar.png"),
        }
        resp = logged_in_client.post(
            f"{API_PREFIX}/profile/avatar", data=data,
            content_type="multipart/form-data")
        assert resp.status_code == 200
        result = resp.get_json()
        assert result["success"] is True
        assert "avatar_url" in result["data"]
        assert result["data"]["user_id"] == user.id
        # Clean up uploaded file
        updated_user = db.session.get(User, user.id)
        if updated_user.avatar_url:
            avatar_path = updated_user.avatar_url.lstrip("/")
            if os.path.exists(avatar_path):
                os.remove(avatar_path)

    def test_upload_avatar_no_file(self, logged_in_client, user):
        resp = logged_in_client.post(
            f"{API_PREFIX}/profile/avatar", data={},
            content_type="multipart/form-data")
        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_upload_avatar_unauthorized(self, client):
        data = {"avatar": (io.BytesIO(b"data"), "avatar.jpg")}
        resp = client.post(
            f"{API_PREFIX}/profile/avatar", data=data,
            content_type="multipart/form-data")
        assert resp.status_code == 401
