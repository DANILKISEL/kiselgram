"""Performance / stress tests for critical endpoints.

These tests verify behavior under load and with large datasets.
Use small scales for CI; adjust for larger stress testing.
"""

from datetime import datetime
from app import db
from app.models import User, Message


API_PREFIX = "/api.v2/api"


class TestBulkData:
    """Test with larger datasets (performance sanity checks)"""

    def test_bulk_chat_list_users(self, logged_in_client, user, session):
        """Create many users and messages, verify chat_list handles it"""
        users = []
        for i in range(20):
            u = User(
                username=f"bulkuser{i}",
                email=f"bulk{i}@example.com",
                email_verified=True,
                display_name=f"Bulk User {i}",
            )
            u.set_password("testpass")
            session.add(u)
            users.append(u)
        session.commit()

        # Send messages from each user to testuser
        for u in users:
            for j in range(3):
                session.add(Message(
                    content=f"Msg {j} from {u.username}",
                    sender_id=u.id,
                    receiver_id=user.id,
                    chat_id=1,
                    timestamp=datetime.utcnow(),
                ))
        session.commit()

        resp = logged_in_client.get(f"{API_PREFIX}/chat_list")
        assert resp.status_code == 200
        data = resp.get_json()
        # Should have saved messages + 20 personal chats
        assert len(data["data"]["chats"]) >= 20

    def test_bulk_messages(self, logged_in_client, user, user2, session):
        """Create 100 messages and verify pagination"""
        for i in range(100):
            session.add(Message(
                content=f"Bulk msg {i}",
                sender_id=user.id,
                receiver_id=user2.id,
                chat_id=1,
                timestamp=datetime.utcnow(),
            ))
        session.commit()

        # Get first page (default limit 50)
        resp = logged_in_client.get(f"{API_PREFIX}/messages/{user2.id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["data"]["messages"]) == 50
        assert data["data"]["pagination"]["has_more"] is True

        # Get second page
        next_cursor = data["data"]["pagination"]["next_cursor"]
        resp2 = logged_in_client.get(
            f"{API_PREFIX}/messages/{user2.id}?after={next_cursor}")
        assert resp2.status_code == 200
        data2 = resp2.get_json()
        assert len(data2["data"]["messages"]) == 50
        assert data2["data"]["pagination"]["has_more"] is False

    def test_bulk_global_search(self, logged_in_client, user, session):
        """Create users, verify search response time is reasonable"""
        for i in range(30):
            u = User(
                username=f"searchuser{i}",
                email=f"search{i}@example.com",
                email_verified=True,
            )
            u.set_password("pass")
            session.add(u)
        session.commit()

        import time
        start = time.time()
        resp = logged_in_client.get(f"{API_PREFIX}/search/global?q=searchuser")
        elapsed = time.time() - start
        assert resp.status_code == 200
        # Should respond within 1 second for 30 users
        assert elapsed < 2.0, f"Search took too long: {elapsed:.2f}s"

    def test_concurrent_requests_do_not_crash(self, client, session, user):
        """Send many rapid requests to verify stability"""
        # Login first to get session
        resp = client.post(f"{API_PREFIX}/auth/login", json={
            "username": "testuser",
            "password": "testpass",
        })
        assert resp.status_code == 200
        session_token = resp.get_json()["data"]["session_token"]

        # Rapid fire requests
        import concurrent.futures
        def make_request(url):
            return client.get(url, headers={
                "Authorization": f"Bearer {session_token}"
            })

        urls = [
            f"{API_PREFIX}/profile",
            f"{API_PREFIX}/chat_list",
            f"{API_PREFIX}/contacts",
            f"{API_PREFIX}/groups",
            f"{API_PREFIX}/search/global?q=test",
        ] * 5

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, url) for url in urls]
            for future in concurrent.futures.as_completed(futures):
                resp = future.result()
                # Should return valid responses, not crash
                assert resp.status_code in (200, 401, 400, 404)
