package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Entity
@Table(name = "pins")
public class Pin {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "message_id", nullable = false)
    private Long messageId;

    @Column(name = "chat_id", nullable = false)
    private Long chatId;

    @Column(name = "pinned_by", nullable = false)
    private Long pinnedBy;

    @Column(name = "pinned_at", nullable = false, updatable = false)
    private LocalDateTime pinnedAt;

    @Column(name = "unpinned_at")
    private LocalDateTime unpinnedAt;

    @Column(name = "is_active")
    private boolean isActive;

    public Pin() {
        this.pinnedAt = LocalDateTime.now();
        this.isActive = true;
    }

    public Pin(Long id, Long messageId, Long chatId, Long pinnedBy, LocalDateTime pinnedAt,
               LocalDateTime unpinnedAt, boolean isActive) {
        this.id = id;
        this.messageId = messageId;
        this.chatId = chatId;
        this.pinnedBy = pinnedBy;
        this.pinnedAt = pinnedAt;
        this.unpinnedAt = unpinnedAt;
        this.isActive = isActive;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("id", id);
        map.put("message_id", messageId);
        map.put("chat_id", chatId);
        map.put("pinned_by", pinnedBy);
        map.put("pinned_at", pinnedAt);
        map.put("unpinned_at", unpinnedAt);
        map.put("is_active", isActive);
        return map;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getMessageId() { return messageId; }
    public void setMessageId(Long messageId) { this.messageId = messageId; }
    public Long getChatId() { return chatId; }
    public void setChatId(Long chatId) { this.chatId = chatId; }
    public Long getPinnedBy() { return pinnedBy; }
    public void setPinnedBy(Long pinnedBy) { this.pinnedBy = pinnedBy; }
    public LocalDateTime getPinnedAt() { return pinnedAt; }
    public void setPinnedAt(LocalDateTime pinnedAt) { this.pinnedAt = pinnedAt; }
    public LocalDateTime getUnpinnedAt() { return unpinnedAt; }
    public void setUnpinnedAt(LocalDateTime unpinnedAt) { this.unpinnedAt = unpinnedAt; }
    public boolean isActive() { return isActive; }
    public void setActive(boolean active) { isActive = active; }
}
