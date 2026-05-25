import json
import os
from datetime import datetime, timedelta
from app import db
from app.models import User, Message, Chat


# ============ /api/utils/health ============

def test_health_check(client):
    resp = client.get("/api/utils/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "database" in data
    assert data["database"] == "connected"
    assert "timestamp" in data
    assert "version" in data


def test_health_check_response_structure(client):
    resp = client.get("/api/utils/health")
    data = resp.get_json()
    assert set(["status", "service", "timestamp", "version",
                 "environment", "python_version", "platform",
                 "database"]).issubset(data.keys())


# ============ /api/utils/ping ============

def test_ping(client):
    resp = client.get("/api/utils/ping")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ping"] == "pong"
    assert "timestamp" in data
    assert "service" in data
    assert "version" in data


# ============ /api/utils/endpoints ============

def test_list_endpoints(client):
    resp = client.get("/api/utils/endpoints")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["prefix"] == "/api/utils"
    assert len(data["endpoints"]) > 0
    endpoint_paths = [e["path"] for e in data["endpoints"]]
    assert "/api/utils/health" in endpoint_paths
    assert "/api/utils/ping" in endpoint_paths
    assert "/api/utils/endpoints" in endpoint_paths
    assert "documentation" in data


# ============ /api/utils/stats (requires token) ============

def test_stats_requires_token(client):
    resp = client.get("/api/utils/stats")
    assert resp.status_code == 401
    assert "Unauthorized" in resp.get_json()["error"]


def test_stats_with_token(client, user):
    token = os.environ.get("KISELGRAM_TOKEN", "default-token-change-me")
    resp = client.get(f"/api/utils/stats?token={token}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "database" in data
    assert "timestamp" in data
    assert data["database"]["users"] >= 1


def test_stats_with_invalid_token(client):
    resp = client.get("/api/utils/stats?token=wrongtoken")
    assert resp.status_code == 401


def test_stats_reflects_data(logged_in_client, user, user2):
    Message(content="test", sender_id=user.id, receiver_id=user2.id)
    db.session.commit()

    token = os.environ.get("KISELGRAM_TOKEN", "default-token-change-me")
    resp = logged_in_client.get(f"/api/utils/stats?token={token}")
    data = resp.get_json()
    assert data["database"]["users"] >= 2


# ============ /api/utils/health/detailed (requires token) ============

def test_detailed_health_requires_token(client):
    resp = client.get("/api/utils/health/detailed")
    assert resp.status_code == 401


def test_detailed_health_with_token(client, user):
    token = os.environ.get("KISELGRAM_TOKEN", "default-token-change-me")
    resp = client.get(f"/api/utils/health/detailed?token={token}")
    # May return 500 if psutil is not installed - that's expected behavior
    if resp.status_code == 500:
        assert "psutil" in resp.get_json().get("error", "")
    else:
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "healthy"
        assert "application" in data


def test_detailed_health_application_info(logged_in_client, user):
    token = os.environ.get("KISELGRAM_TOKEN", "default-token-change-me")
    resp = logged_in_client.get(f"/api/utils/health/detailed?token={token}")
    if resp.status_code == 500:
        assert "psutil" in resp.get_json().get("error", "")
    else:
        data = resp.get_json()
        app_info = data["application"]
        assert "name" in app_info
        assert "database_stats" in app_info


# ============ /api/utils/test/env ============

def test_test_env_get(client):
    resp = client.get("/api/utils/test/env")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["detailed"] == False
    assert "python_version" in data["environment"]
    assert "platform" in data["environment"]
    assert data["environment"]["environment_variables"]["FLASK_ENV"] == "not set"
    assert data["environment"]["environment_variables"]["DATABASE_URL"] == "[REDACTED]"


def test_test_env_post_with_token(client):
    token = os.environ.get("KISELGRAM_TOKEN", "default-token-change-me")
    resp = client.post("/api/utils/test/env",
                       json={"token": token})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["detailed"] == True
    assert "config" in data["environment"]
    assert "sys_path" in data["environment"]


def test_test_env_post_with_header_token(client):
    token = os.environ.get("KISELGRAM_TOKEN", "default-token-change-me")
    resp = client.post("/api/utils/test/env",
                       headers={"X-API-Token": token})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["detailed"] == True


def test_test_env_post_without_token(client):
    resp = client.post("/api/utils/test/env", json={})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["detailed"] == False


def test_test_env_sensitive_keys_redacted(client):
    token = os.environ.get("KISELGRAM_TOKEN", "default-token-change-me")
    resp = client.post("/api/utils/test/env",
                       json={"token": token})
    data = resp.get_json()
    for key in data["environment"]["config"]:
        assert "KEY" not in key.upper()
        assert "TOKEN" not in key.upper()
        assert "PASSWORD" not in key.upper()
        assert "SECRET" not in key.upper()


# ============ /api/utils/test/env/shutdown (requires token) ============

def test_shutdown_requires_token(client):
    resp = client.get("/api/utils/test/env/shutdown")
    assert resp.status_code == 401


def test_shutdown_with_token_returns_accept(client, user):
    token = os.environ.get("KISELGRAM_TOKEN", "default-token-change-me")
    resp = client.get(f"/api/utils/test/env/shutdown?token={token}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "message" in data
    assert data["pid"] > 0


def test_shutdown_with_header_token(client, user):
    token = os.environ.get("KISELGRAM_TOKEN", "default-token-change-me")
    resp = client.get("/api/utils/test/env/shutdown",
                      headers={"X-API-Token": token})
    assert resp.status_code == 200


# ============ /api/utils/health — degraded scenarios ============

def test_health_check_has_required_fields(client):
    resp = client.get("/api/utils/health")
    data = resp.get_json()
    for field in ["status", "service", "timestamp", "version",
                   "environment", "python_version", "platform",
                   "database"]:
        assert field in data, f"Missing field: {field}"


# ============ /premium/api/check and /premium/api/features ============

def test_premium_check_not_authenticated(client):
    # Endpoint is public (no auth required) - returns 404 for non-existent user
    resp = client.get("/premium/api/check/99999")
    assert resp.status_code == 404


def test_premium_check_user_not_found(logged_in_client):
    resp = logged_in_client.get("/premium/api/check/99999")
    assert resp.status_code == 404


def test_premium_check_free_user(logged_in_client, user):
    resp = logged_in_client.get(f"/premium/api/check/{user.id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_premium"] == False
    assert data["features"] == {}


def test_premium_check_premium_user(logged_in_premium, premium_user):
    resp = logged_in_premium.get(f"/premium/api/check/{premium_user.id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_premium"] == True
    assert len(data["features"]) > 0


def test_premium_features_not_authenticated(client):
    resp = client.get("/premium/api/features")
    assert resp.status_code == 401


def test_premium_features_free_user(logged_in_client, user):
    resp = logged_in_client.get("/premium/api/features")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_premium"] == False
    assert data["features"] == {}


def test_premium_features_premium_user(logged_in_premium, premium_user):
    resp = logged_in_premium.get("/premium/api/features")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_premium"] == True
    assert "bot_api_access" in data["features"]
    assert data["upload_limit"] > 100 * 1024 * 1024


# ============ /premium/api/validate-promo ============

def test_validate_promo_no_code(logged_in_client):
    resp = logged_in_client.post("/premium/api/validate-promo", json={})
    assert resp.status_code == 400


def test_validate_promo_invalid_code(logged_in_client):
    resp = logged_in_client.post("/premium/api/validate-promo", json={"code": "NONEXISTENT"})
    assert resp.status_code == 400
    assert "Invalid" in resp.get_json()["error"]


# ============ /premium/api/activate ============

def test_activate_premium_not_authenticated(client):
    resp = client.post("/premium/api/activate", json={"plan": "monthly"})
    assert resp.status_code == 401


def test_activate_premium_monthly(logged_in_client, user):
    resp = logged_in_client.post("/premium/api/activate", json={"plan": "monthly"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] == True

    db.session.refresh(user)
    assert user.premium is not None
    assert user.premium.is_premium == True
    assert user.premium.premium_plan == "monthly"


def test_activate_premium_yearly(logged_in_client, user):
    resp = logged_in_client.post("/premium/api/activate", json={"plan": "yearly"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] == True

    db.session.refresh(user)
    expires = user.premium.premium_expires_at
    assert (expires - datetime.utcnow()).days >= 364


def test_activate_premium_already_premium(logged_in_premium, premium_user):
    resp = logged_in_premium.post("/premium/api/activate", json={"plan": "yearly"})
    assert resp.status_code == 200
    assert resp.get_json()["success"] == True

    db.session.refresh(premium_user)
    assert premium_user.premium.is_premium == True


def test_activate_premium_check_expiry(logged_in_client, user):
    resp = logged_in_client.post("/premium/api/activate", json={"plan": "monthly"})
    assert resp.status_code == 200

    db.session.refresh(user)
    expires = user.premium.premium_expires_at
    assert expires > datetime.utcnow()
    assert (expires - datetime.utcnow()).days >= 29


def test_premium_auto_expire(logged_in_premium, premium_user, session):
    premium_user.premium.premium_expires_at = datetime.utcnow() - timedelta(days=1)
    db.session.commit()

    check_resp = logged_in_premium.get(f"/premium/api/check/{premium_user.id}")
    data = check_resp.get_json()
    assert data["is_premium"] == False
