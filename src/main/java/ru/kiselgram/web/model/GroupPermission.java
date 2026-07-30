package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.util.HashMap;
import java.util.Map;

@Entity
@Table(name = "group_permissions")
@IdClass(GroupPermissionId.class)
public class GroupPermission {

    @Id
    @ManyToOne
    @JoinColumn(name = "chat_id", nullable = false)
    private Chat chat;

    @Id
    @Column(length = 20)
    private String role;

    @Column(name = "can_send_messages")
    private boolean canSendMessages;

    @Column(name = "can_send_media")
    private boolean canSendMedia;

    @Column(name = "can_add_members")
    private boolean canAddMembers;

    @Column(name = "can_pin_messages")
    private boolean canPinMessages;

    @Column(name = "can_change_info")
    private boolean canChangeInfo;

    @Column(name = "can_delete_messages")
    private boolean canDeleteMessages;

    @Column(name = "can_ban_users")
    private boolean canBanUsers;

    public GroupPermission() {}

    public GroupPermission(Chat chat, String role, boolean canSendMessages, boolean canSendMedia,
                           boolean canAddMembers, boolean canPinMessages, boolean canChangeInfo,
                           boolean canDeleteMessages, boolean canBanUsers) {
        this.chat = chat;
        this.role = role;
        this.canSendMessages = canSendMessages;
        this.canSendMedia = canSendMedia;
        this.canAddMembers = canAddMembers;
        this.canPinMessages = canPinMessages;
        this.canChangeInfo = canChangeInfo;
        this.canDeleteMessages = canDeleteMessages;
        this.canBanUsers = canBanUsers;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("chat_id", chat != null ? chat.getId() : null);
        map.put("role", role);
        map.put("can_send_messages", canSendMessages);
        map.put("can_send_media", canSendMedia);
        map.put("can_add_members", canAddMembers);
        map.put("can_pin_messages", canPinMessages);
        map.put("can_change_info", canChangeInfo);
        map.put("can_delete_messages", canDeleteMessages);
        map.put("can_ban_users", canBanUsers);
        return map;
    }

    public Chat getChat() { return chat; }
    public void setChat(Chat chat) { this.chat = chat; }
    public String getRole() { return role; }
    public void setRole(String role) { this.role = role; }
    public boolean isCanSendMessages() { return canSendMessages; }
    public void setCanSendMessages(boolean canSendMessages) { this.canSendMessages = canSendMessages; }
    public boolean isCanSendMedia() { return canSendMedia; }
    public void setCanSendMedia(boolean canSendMedia) { this.canSendMedia = canSendMedia; }
    public boolean isCanAddMembers() { return canAddMembers; }
    public void setCanAddMembers(boolean canAddMembers) { this.canAddMembers = canAddMembers; }
    public boolean isCanPinMessages() { return canPinMessages; }
    public void setCanPinMessages(boolean canPinMessages) { this.canPinMessages = canPinMessages; }
    public boolean isCanChangeInfo() { return canChangeInfo; }
    public void setCanChangeInfo(boolean canChangeInfo) { this.canChangeInfo = canChangeInfo; }
    public boolean isCanDeleteMessages() { return canDeleteMessages; }
    public void setCanDeleteMessages(boolean canDeleteMessages) { this.canDeleteMessages = canDeleteMessages; }
    public boolean isCanBanUsers() { return canBanUsers; }
    public void setCanBanUsers(boolean canBanUsers) { this.canBanUsers = canBanUsers; }
}

class GroupPermissionId implements java.io.Serializable {
    private Long chat;
    private String role;

    public GroupPermissionId() {}
    public GroupPermissionId(Long chat, String role) { this.chat = chat; this.role = role; }

    public Long getChat() { return chat; }
    public void setChat(Long chat) { this.chat = chat; }
    public String getRole() { return role; }
    public void setRole(String role) { this.role = role; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        GroupPermissionId that = (GroupPermissionId) o;
        return java.util.Objects.equals(chat, that.chat) && java.util.Objects.equals(role, that.role);
    }

    @Override
    public int hashCode() {
        return java.util.Objects.hash(chat, role);
    }
}
