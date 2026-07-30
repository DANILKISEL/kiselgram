package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Entity
@Table(name = "channel_admins")
@IdClass(ChannelAdminId.class)
public class ChannelAdmin {

    @Id
    @ManyToOne
    @JoinColumn(name = "chat_id", nullable = false)
    private Chat chat;

    @Id
    @ManyToOne
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(name = "can_post")
    private boolean canPost;

    @Column(name = "can_edit")
    private boolean canEdit;

    @Column(name = "can_delete")
    private boolean canDelete;

    @Column(name = "can_add_admins")
    private boolean canAddAdmins;

    @Column(name = "added_at", nullable = false, updatable = false)
    private LocalDateTime addedAt;

    public ChannelAdmin() {
        this.addedAt = LocalDateTime.now();
    }

    public ChannelAdmin(Chat chat, User user, boolean canPost, boolean canEdit,
                        boolean canDelete, boolean canAddAdmins, LocalDateTime addedAt) {
        this.chat = chat;
        this.user = user;
        this.canPost = canPost;
        this.canEdit = canEdit;
        this.canDelete = canDelete;
        this.canAddAdmins = canAddAdmins;
        this.addedAt = addedAt;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("chat_id", chat != null ? chat.getId() : null);
        map.put("user_id", user != null ? user.getId() : null);
        map.put("can_post", canPost);
        map.put("can_edit", canEdit);
        map.put("can_delete", canDelete);
        map.put("can_add_admins", canAddAdmins);
        map.put("added_at", addedAt);
        return map;
    }

    public Chat getChat() { return chat; }
    public void setChat(Chat chat) { this.chat = chat; }
    public User getUser() { return user; }
    public void setUser(User user) { this.user = user; }
    public boolean isCanPost() { return canPost; }
    public void setCanPost(boolean canPost) { this.canPost = canPost; }
    public boolean isCanEdit() { return canEdit; }
    public void setCanEdit(boolean canEdit) { this.canEdit = canEdit; }
    public boolean isCanDelete() { return canDelete; }
    public void setCanDelete(boolean canDelete) { this.canDelete = canDelete; }
    public boolean isCanAddAdmins() { return canAddAdmins; }
    public void setCanAddAdmins(boolean canAddAdmins) { this.canAddAdmins = canAddAdmins; }
    public LocalDateTime getAddedAt() { return addedAt; }
    public void setAddedAt(LocalDateTime addedAt) { this.addedAt = addedAt; }
}

class ChannelAdminId implements java.io.Serializable {
    private Long chat;
    private Long user;

    public ChannelAdminId() {}
    public ChannelAdminId(Long chat, Long user) { this.chat = chat; this.user = user; }

    public Long getChat() { return chat; }
    public void setChat(Long chat) { this.chat = chat; }
    public Long getUser() { return user; }
    public void setUser(Long user) { this.user = user; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        ChannelAdminId that = (ChannelAdminId) o;
        return java.util.Objects.equals(chat, that.chat) && java.util.Objects.equals(user, that.user);
    }

    @Override
    public int hashCode() {
        return java.util.Objects.hash(chat, user);
    }
}
