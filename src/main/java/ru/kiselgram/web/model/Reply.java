package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Entity
@Table(name = "replies")
public class Reply {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "original_message_id", nullable = false)
    private Message originalMessage;

    @Column(name = "reply_message_id")
    private Long replyMessageId;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    public Reply() {
        this.createdAt = LocalDateTime.now();
    }

    public Reply(Long id, Message originalMessage, Long replyMessageId, LocalDateTime createdAt) {
        this.id = id;
        this.originalMessage = originalMessage;
        this.replyMessageId = replyMessageId;
        this.createdAt = createdAt;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("id", id);
        map.put("original_message_id", originalMessage != null ? originalMessage.getId() : null);
        map.put("reply_message_id", replyMessageId);
        map.put("created_at", createdAt);
        return map;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Message getOriginalMessage() { return originalMessage; }
    public void setOriginalMessage(Message originalMessage) { this.originalMessage = originalMessage; }
    public Long getReplyMessageId() { return replyMessageId; }
    public void setReplyMessageId(Long replyMessageId) { this.replyMessageId = replyMessageId; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
