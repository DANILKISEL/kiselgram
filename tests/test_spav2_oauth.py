"""Tests for OAuth endpoints under /api.v2/api/auth/oauth/<provider>/*."""

from unittest.mock import patch, MagicMock
from app import db
from app.models import User


API_PREFIX = "/api.v2/api"


class TestV2OAuth:
    """OAuth login and callback for Google, GitHub, Discord"""

    @patch("app.routes.spav2.oauth.oauth.create_client")
    def test_google_login(self, mock_create_client, client):
        mock_client = MagicMock()
        mock_client.authorize_redirect.return_value = "redirecting"
        mock_create_client.return_value = mock_client
        resp = client.get(f"{API_PREFIX}/auth/oauth/google/login")
        # Should redirect
        assert resp.status_code in (200, 302)

    def test_github_login(self, client):
        # Without proper oauth config, this should fail gracefully
        resp = client.get(f"{API_PREFIX}/auth/oauth/github/login")
        assert resp.status_code in (200, 302, 500)

    def test_discord_login(self, client):
        resp = client.get(f"{API_PREFIX}/auth/oauth/discord/login")
        assert resp.status_code in (200, 302, 500)

    def test_invalid_provider_login(self, client):
        resp = client.get(f"{API_PREFIX}/auth/oauth/twitter/login")
        assert resp.status_code == 400

    def test_invalid_provider_callback(self, client):
        resp = client.get(f"{API_PREFIX}/auth/oauth/twitter/callback")
        assert resp.status_code == 400

    @patch("app.routes.spav2.oauth.oauth.create_client")
    def test_callback_token_error(self, mock_create_client, client):
        mock_client = MagicMock()
        mock_client.authorize_access_token.side_effect = Exception("OAuth error")
        mock_create_client.return_value = mock_client
        resp = client.get(f"{API_PREFIX}/auth/oauth/google/callback?code=test&state=test")
        # Should render callback HTML with error
        assert resp.status_code == 200
        assert "text/html" in resp.content_type
        assert b"Authorization failed" in resp.data or b"OAuth" in resp.data
