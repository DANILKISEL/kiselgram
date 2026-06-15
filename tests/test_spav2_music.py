"""Tests for V2 API music endpoints under /api.v2/api/."""

from app import db
from app.models import UserMusic


API_PREFIX = "/api.v2/api"


class TestV2Music:
    """GET/POST /api.v2/api/music/library, DELETE track"""

    def test_list_music_empty(self, logged_in_client, user):
        resp = logged_in_client.get(f"{API_PREFIX}/music/library")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["tracks"] == []

    def test_add_music(self, logged_in_client, user):
        resp = logged_in_client.post(f"{API_PREFIX}/music/library", json={
            "file_url": "/uploads/music/song.mp3",
            "file_name": "song.mp3",
            "artist": "Test Artist",
            "title": "Test Song",
            "duration": 180,
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["title"] == "Test Song"
        track = UserMusic.query.filter_by(user_id=user.id).first()
        assert track is not None

    def test_add_music_duplicate(self, logged_in_client, user):
        db.session.add(UserMusic(user_id=user.id, file_url="/uploads/music/song.mp3",
                  title="Song", added_at=__import__("datetime").datetime.utcnow()))
        db.session.commit()
        resp = logged_in_client.post(f"{API_PREFIX}/music/library", json={
            "file_url": "/uploads/music/song.mp3",
        })
        assert resp.status_code == 400
        assert resp.get_json()["error"]["code"] == "ALREADY_EXISTS"

    def test_add_music_no_url(self, logged_in_client, user):
        resp = logged_in_client.post(f"{API_PREFIX}/music/library", json={})
        assert resp.status_code == 400

    def test_get_music_with_tracks(self, logged_in_client, user):
        from datetime import datetime
        db.session.add(UserMusic(
            user_id=user.id, file_url="/uploads/music/track1.mp3",
            title="Track 1", added_at=datetime.utcnow()))
        db.session.commit()
        resp = logged_in_client.get(f"{API_PREFIX}/music/library")
        data = resp.get_json()
        assert len(data["data"]["tracks"]) == 1

    def test_remove_music(self, logged_in_client, user):
        from datetime import datetime
        track = UserMusic(
            user_id=user.id, file_url="/uploads/music/del.mp3",
            title="Delete Me", added_at=datetime.utcnow())
        db.session.add(track)
        db.session.commit()
        resp = logged_in_client.delete(f"{API_PREFIX}/music/library/{track.id}")
        assert resp.status_code == 200
        assert UserMusic.query.get(track.id) is None

    def test_remove_music_not_found(self, logged_in_client, user):
        resp = logged_in_client.delete(f"{API_PREFIX}/music/library/99999")
        assert resp.status_code == 404

    def test_remove_music_unauthorized(self, client):
        resp = client.delete(f"{API_PREFIX}/music/library/1")
        assert resp.status_code == 401
