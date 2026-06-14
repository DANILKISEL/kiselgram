"""Tests for V2 API search endpoints under /api.v2/api/."""

from datetime import datetime
from app import db
from app.models import User, Message, Contact


API_PREFIX = "/api.v2/api"


class TestV2GlobalSearch:
    """GET /api.v2/api/search/global"""

    def test_global_search_users(self, logged_in_client, user, user2):
        resp = logged_in_client.get(f"{API_PREFIX}/search/global?q=friend")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["data"]["results"]["users"]) >= 1
        assert data["data"]["results"]["users"][0]["username"] == "friend"

    def test_global_search_short_query(self, logged_in_client, user):
        resp = logged_in_client.get(f"{API_PREFIX}/search/global?q=a")
        assert resp.status_code == 400

    def test_global_search_no_query(self, logged_in_client, user):
        resp = logged_in_client.get(f"{API_PREFIX}/search/global")
        assert resp.status_code == 400

    def test_global_search_unauthorized(self, client):
        resp = client.get(f"{API_PREFIX}/search/global?q=test")
        assert resp.status_code == 401


class TestV2SearchUsers:
    """GET /api.v2/api/users"""

    def test_search_users(self, logged_in_client, user, user2):
        resp = logged_in_client.get(f"{API_PREFIX}/users?search=friend")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["data"]["users"]) >= 1
        assert data["data"]["users"][0]["username"] == "friend"

    def test_search_users_self_excluded(self, logged_in_client, user):
        resp = logged_in_client.get(f"{API_PREFIX}/users?search=testuser")
        assert resp.status_code == 200
        data = resp.get_json()
        usernames = [u["username"] for u in data["data"]["users"]]
        assert "testuser" not in usernames

    def test_search_users_short_query(self, logged_in_client, user):
        resp = logged_in_client.get(f"{API_PREFIX}/users?search=a")
        assert resp.status_code == 400

    def test_search_users_no_results(self, logged_in_client, user):
        resp = logged_in_client.get(f"{API_PREFIX}/users?search=zzzzz")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["users"] == []


class TestV2GetUserProfile:
    """GET /api.v2/api/users/<user_id>"""

    def test_get_user_profile(self, logged_in_client, user, user2):
        resp = logged_in_client.get(f"{API_PREFIX}/users/{user2.id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["username"] == "friend"
        assert data["data"]["user_id"] == user2.id

    def test_get_user_profile_not_found(self, logged_in_client, user):
        resp = logged_in_client.get(f"{API_PREFIX}/users/99999")
        assert resp.status_code == 404


class TestV2SearchInChat:
    """POST /api.v2/api/search_in_chat"""

    def test_search_in_chat_personal(self, logged_in_client, user, user2):
        for text in ["apple", "banana", "apple pie", "grape"]:
            db.session.add(Message(
                content=text,
                sender_id=user.id if "apple" in text else user2.id,
                receiver_id=user2.id if "apple" in text else user.id,
                chat_id=1, timestamp=datetime.utcnow()))
        db.session.commit()
        resp = logged_in_client.post(f"{API_PREFIX}/search_in_chat", json={
            "chat_id": user2.id,
            "chat_type": "personal",
            "query": "apple",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["data"]["results"]) == 2

    def test_search_in_chat_missing_params(self, logged_in_client, user):
        resp = logged_in_client.post(f"{API_PREFIX}/search_in_chat", json={})
        assert resp.status_code == 400


class TestV2RecentSearches:
    """GET/POST /api.v2/api/recent_searches"""

    def test_add_recent_search(self, logged_in_client, user):
        resp = logged_in_client.post(f"{API_PREFIX}/recent_searches", json={
            "query": "test query",
        })
        assert resp.status_code == 200

    def test_get_recent_searches(self, logged_in_client, user):
        logged_in_client.post(f"{API_PREFIX}/recent_searches", json={
            "query": "hello world",
        })
        resp = logged_in_client.get(f"{API_PREFIX}/recent_searches")
        data = resp.get_json()
        assert len(data["data"]["searches"]) >= 1
        assert data["data"]["searches"][0]["query"] == "hello world"

    def test_recent_searches_empty(self, logged_in_client, user):
        resp = logged_in_client.get(f"{API_PREFIX}/recent_searches")
        assert resp.get_json()["data"]["searches"] == []
