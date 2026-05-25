import json, io
from datetime import datetime
from app import db
from app.models import Message, Story, StoryView, StoryLike, StoryReaction, Contact, BlockedUser, User, Chat, ChatMember



class TestMessaging:
    """Tests for message send / receive / reactions / search endpoints"""

    def test_send_message(self, logged_in_client, user, user2):
        resp = logged_in_client.post("/api/send_message", json={
            "receiver_id": user2.id, "content": "Hello!",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        msg = data["message"]
        assert msg["content"] == "Hello!"
        assert msg["sender_id"] == user.id
        assert msg["receiver_id"] == user2.id

    def test_send_message_with_reply(self, logged_in_client, user, user2):
        from app.models import Reply
        original = Message(content="Original", sender_id=user.id, receiver_id=user2.id, timestamp=datetime.utcnow())
        db.session.add(original)
        db.session.commit()
        resp = logged_in_client.post("/api/send_message", json={
            "receiver_id": user2.id, "content": "Reply!", "reply_to_id": original.id,
        })
        assert resp.status_code == 200
        reply = Reply.query.filter_by(original_message_id=original.id).first()
        assert reply is not None

    def test_send_message_no_content(self, logged_in_client, user, user2):
        resp = logged_in_client.post("/api/send_message", json={
            "receiver_id": user2.id, "content": "",
        })
        assert resp.status_code == 400

    def test_get_messages(self, logged_in_client, user, user2):
        for i in range(3):
            db.session.add(Message(
                content=f"Msg {i}", sender_id=user.id,
                receiver_id=user2.id, timestamp=datetime.utcnow()))
        db.session.commit()
        resp = logged_in_client.get(f"/api/messages/{user2.id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["messages"]) == 3

    def test_get_messages_after_id(self, logged_in_client, user, user2):
        from app import db
        msgs = []
        for i in range(5):
            m = Message(content=f"M{i}", sender_id=user.id, receiver_id=user2.id, timestamp=datetime.utcnow())
            db.session.add(m)
            msgs.append(m)
        db.session.commit()
        after_id = msgs[2].id
        resp = logged_in_client.get(f"/api/messages/{user2.id}?after={after_id}")
        data = resp.get_json()
        assert len(data["messages"]) == 2

    def test_mark_read(self, logged_in_client, user, user2):
        msg = Message(content="Unread", sender_id=user2.id, receiver_id=user.id, timestamp=datetime.utcnow())
        db.session.add(msg)
        db.session.commit()
        resp = logged_in_client.post(f"/api/mark_read/{user2.id}")
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True
        updated = db.session.get(Message, msg.id)
        assert updated.is_read is True

    def test_delete_message(self, logged_in_client, user, user2):
        msg = Message(content="Delete me", sender_id=user.id, receiver_id=user2.id, timestamp=datetime.utcnow())
        db.session.add(msg)
        db.session.commit()
        resp = logged_in_client.delete(f"/api/messages/{msg.id}/delete")
        assert resp.status_code == 200
        updated = db.session.get(Message, msg.id)
        assert updated.is_deleted is True

    def test_delete_others_message(self, logged_in_client, user, user2):
        msg = Message(content="Not yours", sender_id=user2.id, receiver_id=user.id, timestamp=datetime.utcnow())
        db.session.add(msg)
        db.session.commit()
        resp = logged_in_client.delete(f"/api/messages/{msg.id}/delete")
        assert resp.status_code == 403

    def test_reactions(self, logged_in_client, user, user2):
        msg = Message(content="React to me", sender_id=user.id, receiver_id=user2.id, timestamp=datetime.utcnow())
        db.session.add(msg)
        db.session.commit()
        mid = msg.id
        resp = logged_in_client.post("/api/reactions/add", json={
            "message_id": mid, "reaction_type": "❤️",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True

    def test_chat_list(self, logged_in_client, user, user2):
        msg = Message(content="Chat list test", sender_id=user.id, receiver_id=user2.id, timestamp=datetime.utcnow())
        db.session.add(msg)
        db.session.commit()
        resp = logged_in_client.get("/api/chat_list")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert len(data["chats"]) >= 1
        chat = next((c for c in data["chats"] if c["type"] == "personal" and c["id"] == user2.id), None)
        assert chat is not None
        assert chat["name"] == "Friend"

    def test_search_in_chat_personal(self, logged_in_client, user, user2):
        for text in ["apple", "banana", "apple pie", "grape"]:
            db.session.add(Message(content=text, sender_id=user.id if "apple" in text else user2.id,
                                   receiver_id=user2.id if "apple" in text else user.id, timestamp=datetime.utcnow()))
        db.session.commit()
        resp = logged_in_client.post("/api/search_in_chat", json={
            "chat_id": user2.id, "chat_type": "personal", "query": "apple",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["messages"]) == 2

    def test_search_in_chat_group(self, logged_in_client, user, user2):
        g = Chat(chat_type='group', name="SearchGroup", owner_id=user.id)
        db.session.add(g)
        db.session.commit()
        db.session.add(ChatMember(user=user, chat=g, role="owner"))
        db.session.add(ChatMember(user=user2, chat=g, role="member"))
        db.session.add(Message(content="hello world", sender_id=user.id, group_id=g.id, receiver_id=user.id, timestamp=datetime.utcnow()))
        db.session.add(Message(content="goodbye", sender_id=user2.id, group_id=g.id, receiver_id=user2.id, timestamp=datetime.utcnow()))
        db.session.commit()
        resp = logged_in_client.post("/api/search_in_chat", json={
            "chat_id": g.id, "chat_type": "group", "query": "hello",
        })
        assert resp.status_code == 200
        assert len(resp.get_json()["messages"]) == 1

    def test_typing_indicator(self, logged_in_client, user, user2):
        resp = logged_in_client.post(f"/api/typing/personal/{user2.id}")
        assert resp.status_code == 200
        resp = logged_in_client.get(f"/api/typing/personal/{user2.id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["typing"] is not None


class TestStories:
    """Tests for /api/stories endpoints (premium-only)"""

    def test_create_story(self, logged_in_premium, premium_user):
        data = {
            "media": (io.BytesIO(b"fake-image-data"), "test.jpg"),
            "caption": "My first story",
        }
        resp = logged_in_premium.post("/api/stories/create", data=data,
                                     content_type="multipart/form-data")
        assert resp.status_code == 200
        result = resp.get_json()
        assert result["success"] is True
        assert result["story"]["media_type"] == "image"
        assert result["story"]["caption"] == "My first story"

    def test_create_story_no_media(self, logged_in_premium):
        resp = logged_in_premium.post("/api/stories/create", data={})
        assert resp.status_code == 400
        assert "No media" in resp.get_json()["error"]

    def test_create_story_invalid_type(self, logged_in_premium):
        data = {"media": (io.BytesIO(b"data"), "test.exe")}
        resp = logged_in_premium.post("/api/stories/create", data=data,
                                     content_type="multipart/form-data")
        assert resp.status_code == 400

    def test_get_stories(self, logged_in_premium, premium_user, user2):
        s = Story(user_id=user2.id, media_path="stories/test.jpg", media_type="image")
        db.session.add(s)
        db.session.commit()
        db.session.add(Message(content="hi", sender_id=user2.id, receiver_id=premium_user.id, timestamp=datetime.utcnow()))
        db.session.commit()
        resp = logged_in_premium.get("/api/stories")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert len(data["stories"]) >= 1

    def test_view_story(self, logged_in_premium, premium_user, user2):
        s = Story(user_id=user2.id, media_path="s/view.jpg", media_type="image")
        db.session.add(s)
        db.session.commit()
        resp = logged_in_premium.post(f"/api/stories/{s.id}/view")
        assert resp.status_code == 200
        view = StoryView.query.filter_by(story_id=s.id, viewer_id=premium_user.id).first()
        assert view is not None

    def test_like_story(self, logged_in_premium, premium_user, user2):
        s = Story(user_id=user2.id, media_path="s/like.jpg", media_type="image")
        db.session.add(s)
        db.session.commit()
        resp = logged_in_premium.post(f"/api/stories/{s.id}/like")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["liked"] is True
        assert data["like_count"] == 1
        resp = logged_in_premium.post(f"/api/stories/{s.id}/like")
        assert resp.get_json()["liked"] is False

    def test_story_reaction(self, logged_in_premium, premium_user, user2):
        s = Story(user_id=user2.id, media_path="s/react.jpg", media_type="image")
        db.session.add(s)
        db.session.commit()
        resp = logged_in_premium.post(f"/api/stories/{s.id}/reaction", json={"reaction": "❤️"})
        assert resp.status_code == 200
        reaction = StoryReaction.query.filter_by(story_id=s.id, user_id=premium_user.id).first()
        assert reaction is not None
        assert reaction.reaction == "❤️"
        resp = logged_in_premium.post(f"/api/stories/{s.id}/reaction", json={"reaction": "X"})
        assert resp.status_code == 400

    def test_reply_to_story(self, logged_in_premium, premium_user, user2):
        s = Story(user_id=user2.id, media_path="s/reply.jpg", media_type="image")
        db.session.add(s)
        db.session.commit()
        resp = logged_in_premium.post(f"/api/stories/{s.id}/reply", json={"reply_text": "Nice!"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["chat_id"] == user2.id
        msg = Message.query.filter_by(sender_id=premium_user.id, receiver_id=user2.id).first()
        assert msg is not None
        assert "Nice!" in msg.content

    def test_story_stats(self, logged_in_premium, premium_user):
        s = Story(user_id=premium_user.id, media_path="s/stats.jpg", media_type="image")
        db.session.add(s)
        db.session.commit()
        resp = logged_in_premium.get(f"/api/stories/{s.id}/stats")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "viewers" in data

    def test_story_stats_not_owner(self, logged_in_premium, premium_user, user2):
        s = Story(user_id=user2.id, media_path="s/stats2.jpg", media_type="image")
        db.session.add(s)
        db.session.commit()
        resp = logged_in_premium.get(f"/api/stories/{s.id}/stats")
        assert resp.status_code == 403

    def test_delete_story(self, logged_in_premium, premium_user):
        s = Story(user_id=premium_user.id, media_path="s/del.jpg", media_type="image")
        db.session.add(s)
        db.session.commit()
        sid = s.id
        resp = logged_in_premium.delete(f"/api/stories/{s.id}")
        assert resp.status_code == 200
        assert db.session.get(Story, sid) is None

    def test_delete_story_not_owner(self, logged_in_premium, premium_user, user2):
        s = Story(user_id=user2.id, media_path="s/del2.jpg", media_type="image")
        db.session.add(s)
        db.session.commit()
        resp = logged_in_premium.delete(f"/api/stories/{s.id}")
        assert resp.status_code == 403

    def test_free_user_blocked_from_stories(self, logged_in_client, user, user2):
        s = Story(user_id=user2.id, media_path="s/free.jpg", media_type="image")
        db.session.add(s)
        db.session.commit()
        resp = logged_in_client.get("/api/stories")
        assert resp.status_code == 403
        resp = logged_in_client.post(f"/api/stories/{s.id}/view")
        assert resp.status_code == 403
        resp = logged_in_client.post(f"/api/stories/{s.id}/like")
        assert resp.status_code == 403


class TestContacts:
    """Tests for /api/contacts endpoints"""

    def test_get_contacts_empty(self, logged_in_client):
        resp = logged_in_client.get("/api/contacts")
        assert resp.status_code == 200
        assert resp.get_json()["contacts"] == []

    def test_add_contact(self, logged_in_client, user, user2):
        resp = logged_in_client.post("/api/contacts", json={"contact_id": user2.id})
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True
        c = Contact.query.filter_by(user_id=user.id, contact_id=user2.id).first()
        assert c is not None

    def test_add_contact_self(self, logged_in_client, user):
        resp = logged_in_client.post("/api/contacts", json={"contact_id": user.id})
        assert resp.status_code == 400

    def test_add_contact_duplicate(self, logged_in_client, user, user2):
        db.session.add(Contact(user_id=user.id, contact_id=user2.id))
        db.session.commit()
        resp = logged_in_client.post("/api/contacts", json={"contact_id": user2.id})
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "Already in contacts"

    def test_rename_contact(self, logged_in_client, user, user2):
        db.session.add(Contact(user_id=user.id, contact_id=user2.id))
        db.session.commit()
        resp = logged_in_client.post("/api/contacts/rename", json={
            "contact_id": user2.id, "name": "BFF",
        })
        assert resp.status_code == 200
        c = Contact.query.filter_by(user_id=user.id, contact_id=user2.id).first()
        assert c.custom_name == "BFF"

    def test_block_user(self, logged_in_client, user, user2):
        resp = logged_in_client.post(f"/api/block_user/{user2.id}")
        assert resp.status_code == 200
        block = BlockedUser.query.filter_by(user_id=user.id, blocked_user_id=user2.id).first()
        assert block is not None

    def test_block_self(self, logged_in_client, user):
        resp = logged_in_client.post(f"/api/block_user/{user.id}")
        assert resp.status_code == 400

    def test_block_duplicate(self, logged_in_client, user, user2):
        db.session.add(BlockedUser(user_id=user.id, blocked_user_id=user2.id))
        db.session.commit()
        resp = logged_in_client.post(f"/api/block_user/{user2.id}")
        assert resp.status_code == 400

    def test_unblock_user(self, logged_in_client, user, user2):
        db.session.add(BlockedUser(user_id=user.id, blocked_user_id=user2.id))
        db.session.commit()
        resp = logged_in_client.post(f"/api/unblock_user/{user2.id}")
        assert resp.status_code == 200
        block = BlockedUser.query.filter_by(user_id=user.id, blocked_user_id=user2.id).first()
        assert block is None

    def test_get_blocked_users(self, logged_in_client, user, user2):
        db.session.add(BlockedUser(user_id=user.id, blocked_user_id=user2.id))
        db.session.commit()
        resp = logged_in_client.get("/api/blocked_users")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["blocked_users"]) == 1
