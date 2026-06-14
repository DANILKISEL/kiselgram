"""Tests for utility API endpoints under /api/utils/*."""

from unittest.mock import patch, MagicMock


class TestUtilsHealth:
    """GET /api/utils/health"""

    def test_health_endpoint(self, client):
        resp = client.get("/api/utils/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "healthy"
        assert "service" in data


class TestUtilsPing:
    """GET /api/utils/ping"""

    def test_ping(self, client):
        resp = client.get("/api/utils/ping")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ping"] == "pong"


class TestUtilsEndpoints:
    """GET /api/utils/endpoints"""

    def test_list_endpoints(self, client):
        resp = client.get("/api/utils/endpoints")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["endpoints"]) >= 1


class TestUtilsEnv:
    """GET /api/utils/test/env"""

    def test_env_get(self, client):
        resp = client.get("/api/utils/test/env")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "environment" in data


class TestUtilsDetailedHealth:
    """GET /api/utils/health/detailed — requires token"""

    def test_detailed_health_no_token(self, client):
        resp = client.get("/api/utils/health/detailed")
        assert resp.status_code == 401

    def test_detailed_health_bad_token(self, client):
        resp = client.get("/api/utils/health/detailed",
                          headers={"X-API-Token": "wrong"})
        assert resp.status_code == 401


class TestUtilsStats:
    """GET /api/utils/stats — requires token"""

    def test_stats_no_token(self, client):
        resp = client.get("/api/utils/stats")
        assert resp.status_code == 401
