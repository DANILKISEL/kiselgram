import json
from datetime import datetime
from app import db
from app.models import Group, GroupMember, GroupPermission, Channel, ChannelSubscriber, ChannelAdmin, Message, User


class TestGroups:
    """Tests for /api/groups endpoints"""

    def test_create_group(self, logged_in_client, user):
        resp = logged_in_client.post("/api/groups/create", json={
            "name": "Test Group",
            "description": "A test group",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["group"]["name"] == "Test Group"
        group_id = data["group"]["id"]
        # Verify membership
        members = GroupMember.query.filter_by(group_id=group_id).all()
        assert len(members) == 1
        assert members[0].user_id == user.id
        assert members[0].role == "owner"
        # Verify default permissions
        perms = GroupPermission.query.filter_by(group_id=group_id).all()
        assert len(perms) == 3  # owner, admin, member

    def test_create_group_short_name(self, logged_in_client):
        resp = logged_in_client.post("/api/groups/create", json={"name": "AB"})
        assert resp.status_code == 400
        assert "3 characters" in resp.get_json()["error"]

    def test_create_group_with_members(self, logged_in_client, user, user2, user3):
        resp = logged_in_client.post("/api/groups/create", json={
            "name": "Group With Members",
            "member_ids": [user2.id, user3.id],
        })
        assert resp.status_code == 200
        group_id = resp.get_json()["group"]["id"]
        members = GroupMember.query.filter_by(group_id=group_id).all()
        assert len(members) == 3

    def test_create_group_requires_auth(self, client):
        resp = client.post("/api/groups/create", json={"name": "Test"})
        assert resp.status_code == 401

    def test_get_group(self, logged_in_client, user, user2):
        # Create group first
        resp = logged_in_client.post("/api/groups/create", json={
            "name": "GetTest", "member_ids": [user2.id],
        })
        group_id = resp.get_json()["group"]["id"]
        resp = logged_in_client.get(f"/api/groups/{group_id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["group"]["name"] == "GetTest"
        assert len(data["members"]) == 2
        assert data["user_role"] == "owner"
        assert "permissions" in data

    def test_get_group_not_found(self, logged_in_client):
        resp = logged_in_client.get("/api/groups/99999")
        assert resp.status_code == 404

    def test_get_group_private_not_member(self, logged_in_client, user, user2):
        g = Group(name="Private", owner_id=user2.id, is_public=False)
        db.session.add(g)
        db.session.commit()
        resp = logged_in_client.get(f"/api/groups/{g.id}")
        assert resp.status_code == 403

    def test_group_messages(self, logged_in_client, user, user2):
        g = Group(name="MsgGroup", owner_id=user.id)
        db.session.add(g)
        db.session.commit()
        db.session.add(GroupMember(user=user, group=g, role="owner"))
        db.session.add(GroupMember(user=user2, group=g, role="member"))
        # Add messages
        for i in range(3):
            db.session.add(Message(
                content=f"Msg {i}", sender_id=user.id if i % 2 == 0 else user2.id,
                group_id=g.id, receiver_id=user.id, timestamp=datetime.utcnow()))
        db.session.commit()
        resp = logged_in_client.get(f"/api/group_messages/{g.id}")
        assert resp.status_code == 200
        msgs = resp.get_json()["messages"]
        assert len(msgs) == 3

    def test_send_group_message(self, logged_in_client, user, user2):
        g = Group(name="SendGroup", owner_id=user.id)
        db.session.add(g)
        db.session.commit()
        db.session.add(GroupMember(user=user, group=g, role="owner"))
        db.session.commit()
        resp = logged_in_client.post("/api/send_group_message", json={
            "group_id": g.id, "content": "Hello group!",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["message"]["content"] == "Hello group!"

    def test_send_group_message_not_member(self, logged_in_client, user, user2):
        g = Group(name="ExclGroup", owner_id=user2.id)
        db.session.add(g)
        db.session.commit()
        db.session.add(GroupMember(user=user2, group=g, role="owner"))
        db.session.commit()
        resp = logged_in_client.post("/api/send_group_message", json={
            "group_id": g.id, "content": "Hi",
        })
        assert resp.status_code == 403

    def test_leave_group(self, logged_in_client, user, user2):
        g = Group(name="LeaveGroup", owner_id=user.id)
        db.session.add(g)
        db.session.commit()
        db.session.add(GroupMember(user=user, group=g, role="owner"))
        db.session.add(GroupMember(user=user2, group=g, role="member"))
        db.session.commit()
        # Login as user2
        from tests.conftest import login_as
        login_as(logged_in_client, user2)
        resp = logged_in_client.post(f"/api/leave_group/{g.id}")
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True
        members = GroupMember.query.filter_by(group_id=g.id).all()
        assert len(members) == 1

    def test_join_group(self, logged_in_client, user, user2):
        g = Group(name="JoinGroup", owner_id=user2.id, is_public=True,
                  invite_link="test_invite_link_123")
        db.session.add(g)
        db.session.flush()
        db.session.add(GroupMember(user_id=user2.id, group_id=g.id, role="owner"))
        db.session.commit()
        resp = logged_in_client.get(f"/api/join_group/{g.invite_link}")
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True
        members = GroupMember.query.filter_by(group_id=g.id).all()
        assert len(members) == 2

    def test_join_private_group(self, logged_in_client, user, user2):
        g = Group(name="PrivJoin", owner_id=user2.id, is_public=False,
                  invite_link="private_link_456")
        db.session.add(g)
        db.session.commit()
        # Even with invite link, should join
        resp = logged_in_client.get(f"/api/join_group/{g.invite_link}")
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_update_group(self, logged_in_client, user):
        g = Group(name="OldName", owner_id=user.id)
        db.session.add(g)
        db.session.commit()
        db.session.add(GroupMember(user=user, group=g, role="owner"))
        db.session.commit()
        resp = logged_in_client.post(f"/api/groups/{g.id}/update", json={
            "name": "NewName",
        })
        assert resp.status_code == 200
        assert db.session.get(Group, g.id).name == "NewName"

    def test_update_group_not_owner(self, logged_in_client, user, user2):
        g = Group(name="NoEdit", owner_id=user2.id)
        db.session.add(g)
        db.session.commit()
        db.session.add(GroupMember(user=user2, group=g, role="owner"))
        db.session.commit()
        resp = logged_in_client.post(f"/api/groups/{g.id}/update", json={"name": "Hack"})
        assert resp.status_code == 403

    def test_update_member_role(self, logged_in_client, user, user2):
        g = Group(name="RoleGroup", owner_id=user.id)
        db.session.add(g)
        db.session.commit()
        db.session.add(GroupMember(user=user, group=g, role="owner"))
        db.session.add(GroupMember(user=user2, group=g, role="member"))
        db.session.commit()
        resp = logged_in_client.post(f"/api/groups/{g.id}/members/{user2.id}/role", json={
            "role": "admin",
        })
        assert resp.status_code == 200
        mem = GroupMember.query.filter_by(user_id=user2.id, group_id=g.id).first()
        assert mem.role == "admin"

    def test_remove_member(self, logged_in_client, user, user2):
        g = Group(name="KickGroup", owner_id=user.id)
        db.session.add(g)
        db.session.commit()
        db.session.add(GroupMember(user=user, group=g, role="owner"))
        db.session.add(GroupMember(user=user2, group=g, role="member"))
        db.session.commit()
        resp = logged_in_client.delete(f"/api/groups/{g.id}/members/{user2.id}")
        assert resp.status_code == 200
        members = GroupMember.query.filter_by(group_id=g.id).all()
        assert len(members) == 1

    def test_get_permissions(self, logged_in_client, user):
        g = Group(name="PermGroup", owner_id=user.id)
        db.session.add(g)
        db.session.commit()
        db.session.add(GroupMember(user=user, group=g, role="owner"))
        db.session.commit()
        resp = logged_in_client.get(f"/api/groups/{g.id}/permissions")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "permissions" in data
        assert "owner" in data["permissions"]
        assert "admin" in data["permissions"]
        assert "member" in data["permissions"]
        assert data["permissions"]["owner"]["can_send_messages"] is True

    def test_update_permissions(self, logged_in_client, user):
        g = Group(name="UpPerm", owner_id=user.id)
        db.session.add(g)
        db.session.commit()
        db.session.add(GroupMember(user=user, group=g, role="owner"))
        db.session.commit()
        resp = logged_in_client.post(f"/api/groups/{g.id}/permissions", json={
            "role": "member",
            "permissions": {"can_send_messages": False, "can_send_media": False},
        })
        assert resp.status_code == 200
        perm = GroupPermission.query.filter_by(group_id=g.id, role="member").first()
        assert perm.can_send_messages is False


class TestChannels:
    """Tests for /api/channels endpoints"""

    def test_create_channel(self, logged_in_client, user):
        resp = logged_in_client.post("/api/channels/create", json={
            "name": "News Channel",
            "description": "Daily updates",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["channel"]["name"] == "News Channel"
        channel_id = data["channel"]["id"]
        sub = ChannelSubscriber.query.filter_by(channel_id=channel_id).first()
        assert sub is not None
        assert sub.user_id == user.id

    def test_create_channel_short_name(self, logged_in_client):
        resp = logged_in_client.post("/api/channels/create", json={"name": "AB"})
        assert resp.status_code == 400

    def test_get_channel(self, logged_in_client, user, user2):
        c = Channel(name="GetChan", owner_id=user.id)
        db.session.add(c)
        db.session.commit()
        db.session.add(ChannelSubscriber(user_id=user.id, channel_id=c.id))
        db.session.commit()
        resp = logged_in_client.get(f"/api/channels/{c.id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["channel"]["name"] == "GetChan"
        assert data["is_subscribed"] is True

    def test_get_channel_not_found(self, logged_in_client):
        resp = logged_in_client.get("/api/channels/99999")
        assert resp.status_code == 404

    def test_subscribe(self, logged_in_client, user, user2):
        c = Channel(name="SubChan", owner_id=user2.id)
        db.session.add(c)
        db.session.commit()
        resp = logged_in_client.post(f"/api/channels/{c.id}/subscribe")
        assert resp.status_code == 200
        sub = ChannelSubscriber.query.filter_by(channel_id=c.id, user_id=user.id).first()
        assert sub is not None

    def test_unsubscribe(self, logged_in_client, user, user2):
        c = Channel(name="UnsubChan", owner_id=user2.id)
        db.session.add(c)
        db.session.commit()
        db.session.add(ChannelSubscriber(user_id=user.id, channel_id=c.id))
        db.session.commit()
        resp = logged_in_client.post(f"/api/channels/{c.id}/unsubscribe")
        assert resp.status_code == 200
        sub = ChannelSubscriber.query.filter_by(channel_id=c.id, user_id=user.id).first()
        assert sub is None

    def test_owner_cannot_unsubscribe(self, logged_in_client, user):
        c = Channel(name="OwnerChan", owner_id=user.id)
        db.session.add(c)
        db.session.commit()
        db.session.add(ChannelSubscriber(user_id=user.id, channel_id=c.id))
        db.session.commit()
        resp = logged_in_client.post(f"/api/channels/{c.id}/unsubscribe")
        assert resp.status_code == 400

    def test_channel_messages(self, logged_in_client, user, user2):
        c = Channel(name="MsgChan", owner_id=user.id)
        db.session.add(c)
        db.session.commit()
        db.session.add(ChannelSubscriber(user_id=user.id, channel_id=c.id))
        for i in range(3):
            db.session.add(Message(
                content=f"Chan msg {i}", sender_id=user.id,
                channel_id=c.id, receiver_id=user.id, timestamp=datetime.utcnow()))
        db.session.commit()
        resp = logged_in_client.get(f"/api/channel_messages/{c.id}")
        assert resp.status_code == 200
        msgs = resp.get_json()["messages"]
        assert len(msgs) == 3

    def test_send_channel_message(self, logged_in_client, user):
        c = Channel(name="SendChan", owner_id=user.id)
        db.session.add(c)
        db.session.commit()
        db.session.add(ChannelSubscriber(user_id=user.id, channel_id=c.id))
        db.session.commit()
        resp = logged_in_client.post("/api/send_channel_message", json={
            "channel_id": c.id, "content": "Hello channel!",
        })
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_send_channel_message_not_owner(self, logged_in_client, user, user2):
        c = Channel(name="OtherChan", owner_id=user2.id)
        db.session.add(c)
        db.session.commit()
        db.session.add(ChannelSubscriber(user_id=user2.id, channel_id=c.id))
        resp = logged_in_client.post("/api/send_channel_message", json={
            "channel_id": c.id, "content": "Hi",
        })
        assert resp.status_code == 403

    def test_update_channel(self, logged_in_client, user):
        c = Channel(name="Old", owner_id=user.id)
        db.session.add(c)
        db.session.commit()
        resp = logged_in_client.post(f"/api/channels/{c.id}/update", json={
            "name": "Updated", "is_public": False,
        })
        assert resp.status_code == 200
        updated = db.session.get(Channel, c.id)
        assert updated.name == "Updated"
        assert updated.is_public is False

    def test_update_channel_not_owner(self, logged_in_client, user, user2):
        c = Channel(name="NoTouch", owner_id=user2.id)
        db.session.add(c)
        db.session.commit()
        resp = logged_in_client.post(f"/api/channels/{c.id}/update", json={"name": "Hack"})
        assert resp.status_code == 403

    def test_channel_admins_list(self, logged_in_client, user, user2):
        c = Channel(name="AdminChan", owner_id=user.id)
        db.session.add(c)
        db.session.commit()
        db.session.add(ChannelAdmin(channel_id=c.id, user_id=user2.id))
        db.session.commit()
        resp = logged_in_client.get(f"/api/channels/{c.id}/admins")
        assert resp.status_code == 200
        admins = resp.get_json()["admins"]
        assert len(admins) >= 1  # owner is always an admin

    def test_add_channel_admin(self, logged_in_client, user, user2):
        c = Channel(name="AddAdminChan", owner_id=user.id)
        db.session.add(c)
        db.session.commit()
        resp = logged_in_client.post(f"/api/channels/{c.id}/admins", json={
            "user_id": user2.id, "permissions": {"can_post": True},
        })
        assert resp.status_code == 200
        admin = ChannelAdmin.query.filter_by(channel_id=c.id, user_id=user2.id).first()
        assert admin is not None
        assert admin.can_post is True

    def test_remove_channel_admin(self, logged_in_client, user, user2):
        c = Channel(name="RmAdminChan", owner_id=user.id)
        db.session.add(c)
        db.session.commit()
        db.session.add(ChannelAdmin(channel_id=c.id, user_id=user2.id))
        db.session.commit()
        resp = logged_in_client.delete(f"/api/channels/{c.id}/admins/{user2.id}")
        assert resp.status_code == 200
        admin = ChannelAdmin.query.filter_by(channel_id=c.id, user_id=user2.id).first()
        assert admin is None

    def test_delete_channel(self, logged_in_client, user):
        c = Channel(name="DeleteChan", owner_id=user.id)
        db.session.add(c)
        db.session.commit()
        db.session.add(ChannelSubscriber(user_id=user.id, channel_id=c.id))
        db.session.commit()
        resp = logged_in_client.post(f"/api/channels/{c.id}/delete")
        assert resp.status_code == 200
        assert db.session.get(Channel, c.id) is None

    def test_delete_channel_not_owner(self, logged_in_client, user, user2):
        c = Channel(name="NoDel", owner_id=user2.id)
        db.session.add(c)
        db.session.commit()
        resp = logged_in_client.post(f"/api/channels/{c.id}/delete")
        assert resp.status_code == 403

    def test_requires_auth(self, client):
        for url, method in [
            ("/api/channels/create", "post"),
            ("/api/channels/1", "get"),
            ("/api/channels/1/subscribe", "post"),
        ]:
            resp = getattr(client, method)(url)
            assert resp.status_code == 401, f"{method.upper()} {url} should require auth"
