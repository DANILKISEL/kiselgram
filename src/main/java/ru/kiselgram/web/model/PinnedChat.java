package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Entity
@Table(name = "pinned_chats",
       uniqueConstraints = @UniqueConstraint(columnNames = {"user_id", "chat_id"}))
public class PinnedChat {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @ManyToOne
    @JoinColumn(name = "chat_id", nullable = false)
    private Chat chat;

    @Column(name = "pinned_at", nullable = false, updatable = false)
    private LocalDateTime pinnedAt;

    @Column(name = "sort_order")
    private Integer sortOrder;

    public PinnedChat() {
        this.pinnedAt = LocalDateTime.now();
    }

    public PinnedChat(Long id, User user, Chat chat, LocalDateTime pinnedAt, Integer sortOrder) {
        this.id = id;
        this.user = user;
        this.chat = chat;
        this.pinnedAt = pinnedAt;
        this.sortOrder = sortOrder;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("id", id);
        map.put("user_id", user != null ? user.getId() : null);
        map.put("chat_id", chat != null ? chat.getId() : null);
        map.put("pinned_at", pinnedAt);
        map.put("sort_order", sortOrder);
        return map;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public User getUser() { return user; }
    public void setUser(User user) { this.user = user; }
    public Chat getChat() { return chat; }
    public void setChat(Chat chat) { this.chat = chat; }
    public LocalDateTime getPinnedAt() { return pinnedAt; }
    public void setPinnedAt(LocalDateTime pinnedAt) { this.pinnedAt = pinnedAt; }
    public Integer getSortOrder() { return sortOrder; }
    public void setSortOrder(Integer sortOrder) { this.sortOrder = sortOrder; }
}
