package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

@Entity
@Table(name = "chats")
public class Chat {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "chat_type", length = 20)
    private String chatType;

    @Column(length = 100)
    private String name;

    @Column(columnDefinition = "TEXT")
    private String description;

    @Column(name = "avatar_url", length = 500)
    private String avatarUrl;

    @Column(name = "owner_id")
    private Long ownerId;

    @Column(name = "is_public")
    private boolean isPublic;

    @Column(name = "invite_link", length = 100)
    private String inviteLink;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "user1_id")
    private Long user1Id;

    @Column(name = "user2_id")
    private Long user2Id;

    private boolean archived;

    @Column(name = "muted_until")
    private LocalDateTime mutedUntil;

    @Column(name = "theme_color", length = 20)
    private String themeColor;

    @Column(length = 500)
    private String wallpaper;

    @Column(name = "auto_delete_ttl")
    private Integer autoDeleteTtl;

    @OneToMany(mappedBy = "chat")
    private Set<ChatMember> members = new HashSet<>();

    @OneToMany(mappedBy = "chat")
    private Set<ChatSubscriber> subscribers = new HashSet<>();

    @OneToMany(mappedBy = "chat")
    private Set<Message> messages = new HashSet<>();

    @OneToMany(mappedBy = "chat")
    private Set<GroupPermission> permissions = new HashSet<>();

    @OneToMany(mappedBy = "chat")
    private Set<ChannelAdmin> admins = new HashSet<>();

    @OneToMany(mappedBy = "chat")
    private Set<PinnedChat> pinnedByUsers = new HashSet<>();

    public Chat() {
        this.createdAt = LocalDateTime.now();
    }

    public Chat(Long id, String chatType, String name, String description, String avatarUrl,
                Long ownerId, boolean isPublic, String inviteLink, LocalDateTime createdAt,
                Long user1Id, Long user2Id, boolean archived, LocalDateTime mutedUntil,
                String themeColor, String wallpaper, Integer autoDeleteTtl) {
        this.id = id;
        this.chatType = chatType;
        this.name = name;
        this.description = description;
        this.avatarUrl = avatarUrl;
        this.ownerId = ownerId;
        this.isPublic = isPublic;
        this.inviteLink = inviteLink;
        this.createdAt = createdAt;
        this.user1Id = user1Id;
        this.user2Id = user2Id;
        this.archived = archived;
        this.mutedUntil = mutedUntil;
        this.themeColor = themeColor;
        this.wallpaper = wallpaper;
        this.autoDeleteTtl = autoDeleteTtl;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("id", id);
        map.put("chat_type", chatType);
        map.put("name", name);
        map.put("description", description);
        map.put("avatar_url", avatarUrl);
        map.put("owner_id", ownerId);
        map.put("is_public", isPublic);
        map.put("invite_link", inviteLink);
        map.put("created_at", createdAt);
        map.put("user1_id", user1Id);
        map.put("user2_id", user2Id);
        map.put("archived", archived);
        map.put("muted_until", mutedUntil);
        map.put("theme_color", themeColor);
        map.put("wallpaper", wallpaper);
        map.put("auto_delete_ttl", autoDeleteTtl);
        return map;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getChatType() { return chatType; }
    public void setChatType(String chatType) { this.chatType = chatType; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    public String getAvatarUrl() { return avatarUrl; }
    public void setAvatarUrl(String avatarUrl) { this.avatarUrl = avatarUrl; }
    public Long getOwnerId() { return ownerId; }
    public void setOwnerId(Long ownerId) { this.ownerId = ownerId; }
    public boolean isPublic() { return isPublic; }
    public void setPublic(boolean aPublic) { isPublic = aPublic; }
    public String getInviteLink() { return inviteLink; }
    public void setInviteLink(String inviteLink) { this.inviteLink = inviteLink; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    public Long getUser1Id() { return user1Id; }
    public void setUser1Id(Long user1Id) { this.user1Id = user1Id; }
    public Long getUser2Id() { return user2Id; }
    public void setUser2Id(Long user2Id) { this.user2Id = user2Id; }
    public boolean isArchived() { return archived; }
    public void setArchived(boolean archived) { this.archived = archived; }
    public LocalDateTime getMutedUntil() { return mutedUntil; }
    public void setMutedUntil(LocalDateTime mutedUntil) { this.mutedUntil = mutedUntil; }
    public String getThemeColor() { return themeColor; }
    public void setThemeColor(String themeColor) { this.themeColor = themeColor; }
    public String getWallpaper() { return wallpaper; }
    public void setWallpaper(String wallpaper) { this.wallpaper = wallpaper; }
    public Integer getAutoDeleteTtl() { return autoDeleteTtl; }
    public void setAutoDeleteTtl(Integer autoDeleteTtl) { this.autoDeleteTtl = autoDeleteTtl; }
    public Set<ChatMember> getMembers() { return members; }
    public void setMembers(Set<ChatMember> members) { this.members = members; }
    public Set<ChatSubscriber> getSubscribers() { return subscribers; }
    public void setSubscribers(Set<ChatSubscriber> subscribers) { this.subscribers = subscribers; }
    public Set<Message> getMessages() { return messages; }
    public void setMessages(Set<Message> messages) { this.messages = messages; }
    public Set<GroupPermission> getPermissions() { return permissions; }
    public void setPermissions(Set<GroupPermission> permissions) { this.permissions = permissions; }
    public Set<ChannelAdmin> getAdmins() { return admins; }
    public void setAdmins(Set<ChannelAdmin> admins) { this.admins = admins; }
    public Set<PinnedChat> getPinnedByUsers() { return pinnedByUsers; }
    public void setPinnedByUsers(Set<PinnedChat> pinnedByUsers) { this.pinnedByUsers = pinnedByUsers; }
}
