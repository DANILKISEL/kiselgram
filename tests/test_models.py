import pytest
from app.models import (
    User, Message, Group, GroupMember, GroupPermission,
    Channel, ChannelSubscriber, ChannelAdmin,
    Story, StoryView, StoryLike, StoryReaction,
    Contact, BlockedUser, Call, VideoCall, VideoCallParticipant,
    PinnedChat, RecentSearch, Favorite, Reply, Forward, Report,
)
from datetime import datetime, timedelta
from app import db


class TestUserModel:
    def test_create_user(self, session):
        u = User(username="alice", email="alice@test.com")
        u.set_password("secret")
        session.add(u)
        session.commit()
        assert u.id is not None
        assert u.check_password("secret")
        assert not u.check_password("wrong")
        assert u.email_verified is False
        assert u.is_online is False
        assert u.is_premium is False
        assert u.is_admin is False
        assert u.is_bot is False
        assert u.last_seen is not None

    def test_display_name_fallback(self, session):
        u = User(username="bob", email="bob@test.com")
        assert u.display_name is None
        u.display_name = u.username
        assert u.display_name == "bob"

    def test_unique_username(self, session, user):
        u2 = User(username="testuser", email="other@test.com")
        session.add(u2)
        with pytest.raises(Exception):
            session.commit()
        session.rollback()

    def test_unique_email(self, session, user):
        u2 = User(username="other", email="test@example.com")
        session.add(u2)
        with pytest.raises(Exception):
            session.commit()
        session.rollback()

    def test_premium_user(self, session):
        u = User(username="gold", email="gold@test.com", is_premium=True, premium_plan="yearly")
        session.add(u)
        session.commit()
        assert u.is_premium is True
        assert u.premium_plan == "yearly"

    def test_bot_user(self, session):
        owner = User(username="owner", email="owner@test.com")
        session.add(owner)
        session.flush()
        bot = User(username="mybot", email=None, is_bot=True, bot_owner_id=owner.id)
        session.add(bot)
        session.commit()
        assert bot.is_bot is True
        assert bot.bot_owner_id == owner.id

    def test_privacy_defaults(self, session):
        u = User(username="private", email="private@test.com")
        session.add(u)
        session.commit()
        assert u.privacy_last_seen == "everyone"
        assert u.privacy_photo == "everyone"
        assert u.privacy_calls == "everyone"
        assert u.privacy_messages == "everyone"

    def test_soft_delete(self, session):
        u = User(username="deleteme", email="delete@test.com")
        session.add(u)
        session.commit()
        u.is_deleted = True
        u.deleted_at = datetime.utcnow()
        session.commit()
        assert u.is_deleted is True
        assert u.deleted_at is not None


class TestMessageModel:
    def test_send_personal_message(self, session, user, user2):
        msg = Message(
            content="Hello",
            sender=user,
            receiver=user2,
            timestamp=datetime.utcnow()
        )
        session.add(msg)
        session.commit()
        assert msg.id is not None
        assert msg.is_read is False
        assert msg.has_attachment is False
        assert msg.is_deleted is False
        assert msg.sender_id == user.id
        assert msg.receiver_id == user2.id

    def test_group_message(self, session, user, user2):
        group = Group(name="Test Group", owner_id=user.id)
        session.add(group)
        session.flush()
        msg = Message(
            content="Group hello",
            sender=user,
            group_id=group.id,
            receiver_id=user.id,
            timestamp=datetime.utcnow()
        )
        session.add(msg)
        session.commit()
        assert msg.group_id == group.id

    def test_channel_message(self, session, user):
        channel = Channel(name="Test Channel", owner_id=user.id)
        session.add(channel)
        session.flush()
        msg = Message(
            content="Channel hello",
            sender=user,
            channel_id=channel.id,
            receiver_id=user.id,
            timestamp=datetime.utcnow()
        )
        session.add(msg)
        session.commit()
        assert msg.channel_id == channel.id

    def test_message_attachment(self, session, user, user2):
        msg = Message(
            content="Check this file",
            sender=user,
            receiver=user2,
            timestamp=datetime.utcnow(),
            has_attachment=True,
            file_type="image",
            file_name="photo.jpg",
            file_path="uploads/images/photo.jpg",
            file_size=1024,
        )
        session.add(msg)
        session.commit()
        assert msg.has_attachment is True
        assert msg.file_type == "image"
        assert msg.file_size == 1024

    def test_mark_as_read(self, session, user, user2):
        msg = Message(content="Unread", sender_id=user2.id, receiver_id=user.id, timestamp=datetime.utcnow())
        session.add(msg)
        session.commit()
        assert msg.is_read is False
        msg.is_read = True
        msg.read_at = datetime.utcnow()
        session.commit()
        assert msg.is_read is True

    def test_edit_message(self, session, user, user2):
        msg = Message(content="Original", sender=user, receiver=user2, timestamp=datetime.utcnow())
        session.add(msg)
        session.commit()
        msg.content = "Edited"
        msg.edited_at = datetime.utcnow()
        session.commit()
        assert msg.content == "Edited"
        assert msg.edited_at is not None

    def test_soft_delete_message(self, session, user, user2):
        msg = Message(content="Delete me", sender=user, receiver=user2, timestamp=datetime.utcnow())
        session.add(msg)
        session.commit()
        msg.is_deleted = True
        msg.deleted_for_all = True
        session.commit()
        assert msg.is_deleted is True
        assert msg.deleted_for_all is True

    def test_reply(self, session, user, user2):
        original = Message(content="Original", sender=user, receiver=user2, timestamp=datetime.utcnow())
        session.add(original)
        session.flush()
        reply_msg = Message(content="Reply", sender=user2, receiver=user, timestamp=datetime.utcnow())
        session.add(reply_msg)
        session.flush()
        reply = Reply(original_message_id=original.id, reply_message_id=reply_msg.id)
        session.add(reply)
        session.commit()
        assert reply.id is not None

    def test_forward(self, session, user, user2):
        original = Message(content="Forward me", sender=user, receiver=user2, timestamp=datetime.utcnow())
        session.add(original)
        session.flush()
        fwd = Forward(
            original_message_id=original.id,
            forwarded_message_id=original.id,
            forwarded_by_id=user2.id,
            original_sender_name=user.display_name,
        )
        session.add(fwd)
        session.commit()
        assert fwd.id is not None
        assert fwd.original_sender_name == "Test User"


class TestGroupModel:
    def test_create_group(self, session, user):
        import secrets
        group = Group(name="Gamers", owner_id=user.id, description="For gamers", is_public=True, invite_link=secrets.token_urlsafe(16))
        session.add(group)
        session.commit()
        assert group.id is not None
        assert group.invite_link is not None
        assert len(group.invite_link) == 22

    def test_add_member(self, session, user, user2):
        import secrets
        group = Group(name="Group", owner_id=user.id, invite_link=secrets.token_urlsafe(16))
        session.add(group)
        session.flush()
        gm = GroupMember(user=user, group=group, role="owner")
        session.add(gm)
        gm2 = GroupMember(user=user2, group=group, role="member")
        session.add(gm2)
        session.commit()
        assert group.members[0].user == user
        assert group.members[0].role == "owner"
        assert len(group.members.all()) == 2

    def test_duplicate_membership(self, session, user):
        group = Group(name="G", owner_id=user.id)
        session.add(group)
        session.flush()
        session.add(GroupMember(user=user, group=group, role="owner"))
        session.commit()
        dup = GroupMember(user=user, group=group, role="member")
        session.add(dup)
        with pytest.raises(Exception):
            session.commit()
        session.rollback()

    def test_group_permissions(self, session, user):
        group = Group(name="PermGroup", owner_id=user.id)
        session.add(group)
        session.flush()
        perms = GroupPermission(
            group_id=group.id, role="member",
            can_send_messages=True, can_send_media=False,
        )
        session.add(perms)
        session.commit()
        assert perms.can_send_messages is True
        assert perms.can_send_media is False


class TestChannelModel:
    def test_create_channel(self, session, user):
        import secrets
        channel = Channel(name="News Channel", owner_id=user.id, description="Daily news", invite_link=secrets.token_urlsafe(16))
        session.add(channel)
        session.commit()
        assert channel.id is not None
        assert channel.invite_link is not None

    def test_subscribe(self, session, user, user2):
        channel = Channel(name="C", owner_id=user.id)
        session.add(channel)
        session.flush()
        sub = ChannelSubscriber(user=user2, channel=channel)
        session.add(sub)
        session.commit()
        assert sub.id is not None
        assert channel.subscribers[0].user_id == user2.id

    def test_channel_admin(self, session, user, user2):
        channel = Channel(name="AdminChan", owner_id=user.id)
        session.add(channel)
        session.flush()
        admin = ChannelAdmin(
            channel_id=channel.id, user_id=user2.id,
            can_post=True, can_edit=True, can_delete=False,
        )
        session.add(admin)
        session.commit()
        assert admin.can_post is True
        assert admin.can_delete is False


class TestStoryModel:
    def test_create_story(self, session, user):
        story = Story(
            user_id=user.id,
            media_path="stories/test.jpg",
            media_type="image",
            caption="My story",
        )
        session.add(story)
        session.commit()
        assert story.id is not None
        assert story.created_at is not None

    def test_view_story(self, session, user, user2):
        story = Story(user_id=user.id, media_path="s/test.jpg", media_type="image")
        session.add(story)
        session.flush()
        view = StoryView(story=story, viewer=user2)
        session.add(view)
        session.commit()
        assert view.viewed_at is not None
        assert view.viewer_id == user2.id

    def test_like_story(self, session, user, user2):
        story = Story(user_id=user.id, media_path="s/test.jpg", media_type="image")
        session.add(story)
        session.flush()
        like = StoryLike(story=story, user=user2)
        session.add(like)
        session.commit()
        assert like.id is not None

    def test_duplicate_like(self, session, user, user2):
        story = Story(user_id=user.id, media_path="s/test.jpg", media_type="image")
        session.add(story)
        session.flush()
        session.add(StoryLike(story=story, user=user2))
        session.commit()
        dup = StoryLike(story=story, user=user2)
        session.add(dup)
        with pytest.raises(Exception):
            session.commit()
        session.rollback()

    def test_story_reaction(self, session, user, user2):
        story = Story(user_id=user.id, media_path="s/test.jpg", media_type="image")
        session.add(story)
        session.flush()
        reaction = StoryReaction(story=story, user=user2, reaction="❤️")
        session.add(reaction)
        session.commit()
        assert reaction.reaction == "❤️"


class TestContactBlockModel:
    def test_add_contact(self, session, user, user2):
        c = Contact(user_id=user.id, contact_id=user2.id)
        session.add(c)
        session.commit()
        assert c.id is not None

    def test_unique_contact(self, session, user, user2):
        session.add(Contact(user_id=user.id, contact_id=user2.id))
        session.commit()
        dup = Contact(user_id=user.id, contact_id=user2.id)
        session.add(dup)
        with pytest.raises(Exception):
            session.commit()
        session.rollback()

    def test_block_user(self, session, user, user2):
        b = BlockedUser(user_id=user.id, blocked_user_id=user2.id)
        session.add(b)
        session.commit()
        assert b.id is not None

    def test_self_block(self, session, user):
        b = BlockedUser(user_id=user.id, blocked_user_id=user.id)
        session.add(b)
        session.commit()
        assert b.id is not None


class TestCallModel:
    def test_create_call(self, session, user, user2):
        call = Call(caller_id=user.id, receiver_id=user2.id, call_type="audio", status="ringing")
        session.add(call)
        session.commit()
        assert call.id is not None
        assert call.status == "ringing"

    def test_end_call(self, session, user, user2):
        call = Call(caller_id=user.id, receiver_id=user2.id, call_type="video", status="answered")
        session.add(call)
        session.commit()
        call.status = "ended"
        call.duration = 120
        session.commit()
        assert call.status == "ended"
        assert call.duration == 120


class TestPinnedFavoriteSearch:
    def test_pin_chat(self, session, user):
        pc = PinnedChat(user_id=user.id, chat_type="personal", chat_id=42)
        session.add(pc)
        session.commit()
        assert pc.id is not None

    def test_unique_pin(self, session, user):
        session.add(PinnedChat(user_id=user.id, chat_type="personal", chat_id=1))
        session.commit()
        dup = PinnedChat(user_id=user.id, chat_type="personal", chat_id=1)
        session.add(dup)
        with pytest.raises(Exception):
            session.commit()
        session.rollback()

    def test_favorite(self, session, user):
        fav = Favorite(user_id=user.id, file_type="image", file_path="img.jpg", file_name="pic")
        session.add(fav)
        session.commit()
        assert fav.id is not None

    def test_recent_search(self, session, user):
        rs = RecentSearch(user_id=user.id, search_query="hello", search_type="all")
        session.add(rs)
        session.commit()
        assert rs.id is not None


class TestReportModel:
    def test_create_report(self, session, user, user2):
        r = Report(reporter=user, reported_user=user2, reason="spam", status="open")
        session.add(r)
        session.commit()
        assert r.id is not None
        assert r.status == "open"
        assert r.reporter_id == user.id
        assert r.reported_user_id == user2.id
