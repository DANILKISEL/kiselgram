package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Entity
@Table(name = "archives")
public class Archive {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(name = "chat_id", nullable = false)
    private Long chatId;

    @Column(name = "archived_at", nullable = false, updatable = false)
    private LocalDateTime archivedAt;

    @Column(name = "is_archived")
    private boolean isArchived;

    public Archive() {
        this.archivedAt = LocalDateTime.now();
        this.isArchived = true;
    }

    public Archive(Long id, Long userId, Long chatId, LocalDateTime archivedAt, boolean isArchived) {
        this.id = id;
        this.userId = userId;
        this.chatId = chatId;
        this.archivedAt = archivedAt;
        this.isArchived = isArchived;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("id", id);
        map.put("user_id", userId);
        map.put("chat_id", chatId);
        map.put("archived_at", archivedAt);
        map.put("is_archived", isArchived);
        return map;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getUserId() { return userId; }
    public void setUserId(Long userId) { this.userId = userId; }
    public Long getChatId() { return chatId; }
    public void setChatId(Long chatId) { this.chatId = chatId; }
    public LocalDateTime getArchivedAt() { return archivedAt; }
    public void setArchivedAt(LocalDateTime archivedAt) { this.archivedAt = archivedAt; }
    public boolean isArchived() { return isArchived; }
    public void setArchived(boolean archived) { isArchived = archived; }
}
