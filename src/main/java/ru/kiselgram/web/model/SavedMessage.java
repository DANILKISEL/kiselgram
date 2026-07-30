package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Entity
@Table(name = "saved_messages")
public class SavedMessage {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(name = "message_id", nullable = false)
    private Long messageId;

    @Column(name = "saved_at", nullable = false, updatable = false)
    private LocalDateTime savedAt;

    @Column(length = 20)
    private String folder;

    public SavedMessage() {
        this.savedAt = LocalDateTime.now();
    }

    public SavedMessage(Long id, Long userId, Long messageId, LocalDateTime savedAt, String folder) {
        this.id = id;
        this.userId = userId;
        this.messageId = messageId;
        this.savedAt = savedAt;
        this.folder = folder;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("id", id);
        map.put("user_id", userId);
        map.put("message_id", messageId);
        map.put("saved_at", savedAt);
        map.put("folder", folder);
        return map;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getUserId() { return userId; }
    public void setUserId(Long userId) { this.userId = userId; }
    public Long getMessageId() { return messageId; }
    public void setMessageId(Long messageId) { this.messageId = messageId; }
    public LocalDateTime getSavedAt() { return savedAt; }
    public void setSavedAt(LocalDateTime savedAt) { this.savedAt = savedAt; }
    public String getFolder() { return folder; }
    public void setFolder(String folder) { this.folder = folder; }
}
