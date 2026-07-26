"""Tests for V2 API story endpoints under /api.v2/api/."""

import io
from datetime import datetime, timedelta
from app import db
from app.models import Story, StoryView, StoryLike, StoryReaction, Message


API_PREFIX = "/api.v2/api"


class TestV2Stories:
    """GET/POST story endpoints"""

    def test_get_stories_empty(self, logged_in_client, user):
        resp = logged_in_client.get(f"{API_PREFIX}/stories")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["stories"] == []

    def test_get_stories_with_data(self, logged_in_client, user, user2):
        s = Story(user_id=user2.id, media_path="stories/test.jpg",
                  media_type="image", created_at=datetime.utcnow())
        db.session.add(s)
        db.session.commit()
        # Need a message between users to have visible stories
        db.session.add(Message(content="hi", sender_id=user2.id,
                               receiver_id=user.id, chat_id=1, timestamp=datetime.utcnow()))
        db.session.commit()
        resp = logged_in_client.get(f"{API_PREFIX}/stories")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["data"]["stories"]) >= 1

    def test_create_story(self, logged_in_premium, premium_user):
        data = {
            "media": (io.BytesIO(b"fake-image-data"), "story.jpg"),
            "caption": "My V2 story",
        }
        resp = logged_in_premium.post(
            f"{API_PREFIX}/stories/create", data=data,
            content_type="multipart/form-data")
        assert resp.status_code == 201
        result = resp.get_json()
        assert result["success"] is True
        assert result["data"]["story"]["media_type"] == "image"
        assert result["data"]["story"]["caption"] == "My V2 story"

    def test_create_story_no_media(self, logged_in_premium, premium_user):
        resp = logged_in_premium.post(
            f"{API_PREFIX}/stories/create", data={})
        assert resp.status_code == 400

    def test_create_story_invalid_type(self, logged_in_premium, premium_user):
        data = {"media": (io.BytesIO(b"data"), "story.exe")}
        resp = logged_in_premium.post(
            f"{API_PREFIX}/stories/create", data=data,
            content_type="multipart/form-data")
        assert resp.status_code == 400

    def test_create_story_unauthorized(self, client):
        data = {"media": (io.BytesIO(b"data"), "story.jpg")}
        resp = client.post(
            f"{API_PREFIX}/stories/create", data=data,
            content_type="multipart/form-data")
        assert resp.status_code == 401

    def test_view_story(self, logged_in_client, user, user2):
        s = Story(user_id=user2.id, media_path="s/view.jpg",
                  media_type="image", created_at=datetime.utcnow())
        db.session.add(s)
        db.session.commit()
        resp = logged_in_client.post(f"{API_PREFIX}/stories/{s.id}/view")
        assert resp.status_code == 200
        view = StoryView.query.filter_by(
            story_id=s.id, viewer_id=user.id).first()
        assert view is not None

    def test_like_story(self, logged_in_client, user, user2):
        s = Story(user_id=user2.id, media_path="s/like.jpg",
                  media_type="image", created_at=datetime.utcnow())
        db.session.add(s)
        db.session.commit()
        resp = logged_in_client.post(f"{API_PREFIX}/stories/{s.id}/like")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["liked"] is True
        assert data["data"]["like_count"] == 1
        # Toggle off
        resp2 = logged_in_client.post(f"{API_PREFIX}/stories/{s.id}/like")
        assert resp2.get_json()["data"]["liked"] is False

    def test_story_reaction(self, logged_in_client, user, user2):
        s = Story(user_id=user2.id, media_path="s/react.jpg",
                  media_type="image", created_at=datetime.utcnow())
        db.session.add(s)
        db.session.commit()
        valid_reactions = ["heart", "fire", "laugh", "wow", "sad", "angry"]
        for reaction in valid_reactions:
            resp = logged_in_client.post(
                f"{API_PREFIX}/stories/{s.id}/reaction",
                json={"reaction": reaction})
            assert resp.status_code == 200
            stored = StoryReaction.query.filter_by(
                story_id=s.id, user_id=user.id).first()
            assert stored.reaction == reaction

    def test_story_reaction_invalid(self, logged_in_client, user, user2):
        s = Story(user_id=user2.id, media_path="s/react2.jpg",
                  media_type="image", created_at=datetime.utcnow())
        db.session.add(s)
        db.session.commit()
        resp = logged_in_client.post(
            f"{API_PREFIX}/stories/{s.id}/reaction",
            json={"reaction": "invalid_emoji"})
        assert resp.status_code == 400

    def test_reply_to_story(self, logged_in_client, user, user2):
        s = Story(user_id=user2.id, media_path="s/reply.jpg",
                  media_type="image", created_at=datetime.utcnow())
        db.session.add(s)
        db.session.commit()
        resp = logged_in_client.post(
            f"{API_PREFIX}/stories/{s.id}/reply",
            json={"reply_text": "Nice!"})
        assert resp.status_code == 200
        msg = Message.query.filter_by(
            sender_id=user.id, receiver_id=user2.id).first()
        assert msg is not None
        assert "Nice!" in msg.content

    def test_reply_to_story_no_text(self, logged_in_client, user, user2):
        s = Story(user_id=user2.id, media_path="s/reply2.jpg",
                  media_type="image", created_at=datetime.utcnow())
        db.session.add(s)
        db.session.commit()
        resp = logged_in_client.post(
            f"{API_PREFIX}/stories/{s.id}/reply",
            json={"reply_text": ""})
        assert resp.status_code == 400

    def test_story_stats(self, logged_in_client, user):
        s = Story(user_id=user.id, media_path="s/stats.jpg",
                  media_type="image", created_at=datetime.utcnow())
        db.session.add(s)
        db.session.commit()
        resp = logged_in_client.get(f"{API_PREFIX}/stories/{s.id}/stats")
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_story_stats_not_owner(self, logged_in_client, user, user2):
        s = Story(user_id=user2.id, media_path="s/stats2.jpg",
                  media_type="image", created_at=datetime.utcnow())
        db.session.add(s)
        db.session.commit()
        resp = logged_in_client.get(f"{API_PREFIX}/stories/{s.id}/stats")
        assert resp.status_code == 403

    def test_delete_story(self, logged_in_client, user):
        s = Story(user_id=user.id, media_path="s/del.jpg",
                  media_type="image", created_at=datetime.utcnow())
        db.session.add(s)
        db.session.commit()
        sid = s.id
        resp = logged_in_client.delete(f"{API_PREFIX}/stories/{s.id}")
        assert resp.status_code == 200
        assert db.session.get(Story, sid) is None

    def test_delete_story_not_owner(self, logged_in_client, user, user2):
        s = Story(user_id=user2.id, media_path="s/del2.jpg",
                  media_type="image", created_at=datetime.utcnow())
        db.session.add(s)
        db.session.commit()
        resp = logged_in_client.delete(f"{API_PREFIX}/stories/{s.id}")
        assert resp.status_code == 403

    def test_get_stories_unauthorized(self, client):
        resp = client.get(f"{API_PREFIX}/stories")
        assert resp.status_code == 401
