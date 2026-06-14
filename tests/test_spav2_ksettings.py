"""Tests for V2 KSettings endpoints under /api.v2/api/."""

from app import db
from app.models import UserKSettings


API_PREFIX = "/api.v2/api"


class TestV2KSettings:
    """GET/PUT /api.v2/api/k/settings"""

    def test_get_settings_default(self, logged_in_client, user):
        resp = logged_in_client.get(f"{API_PREFIX}/k/settings")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        # Should create default settings
        ks = UserKSettings.query.filter_by(user_id=user.id).first()
        assert ks is not None

    def test_save_settings(self, logged_in_client, user):
        resp = logged_in_client.put(f"{API_PREFIX}/k/settings", json={
            "settings": {"theme": "light", "language": "en"},
        })
        assert resp.status_code == 200
        ks = UserKSettings.query.filter_by(user_id=user.id).first()
        assert ks.settings == {"theme": "light", "language": "en"}

    def test_save_settings_missing_field(self, logged_in_client, user):
        resp = logged_in_client.put(f"{API_PREFIX}/k/settings", json={})
        assert resp.status_code == 400

    def test_get_after_save(self, logged_in_client, user):
        logged_in_client.put(f"{API_PREFIX}/k/settings", json={
            "settings": {"theme": "dark"},
        })
        resp = logged_in_client.get(f"{API_PREFIX}/k/settings")
        data = resp.get_json()
        assert data["data"]["settings"]["theme"] == "dark"

    def test_ksettings_unauthorized(self, client):
        resp = client.get(f"{API_PREFIX}/k/settings")
        assert resp.status_code == 401
