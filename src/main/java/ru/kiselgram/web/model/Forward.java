package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Entity
@Table(name = "forwards")
public class Forward {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "original_message_id", nullable = false)
    private Message originalMessage;

    @Column(name = "forwarded_message_id")
    private Long forwardedMessageId;

    @Column(name = "forwarded_by_id")
    private Long forwardedById;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "original_sender_name", length = 100)
    private String originalSenderName;

    public Forward() {
        this.createdAt = LocalDateTime.now();
    }

    public Forward(Long id, Message originalMessage, Long forwardedMessageId,
                   Long forwardedById, LocalDateTime createdAt, String originalSenderName) {
        this.id = id;
        this.originalMessage = originalMessage;
        this.forwardedMessageId = forwardedMessageId;
        this.forwardedById = forwardedById;
        this.createdAt = createdAt;
        this.originalSenderName = originalSenderName;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("id", id);
        map.put("original_message_id", originalMessage != null ? originalMessage.getId() : null);
        map.put("forwarded_message_id", forwardedMessageId);
        map.put("forwarded_by_id", forwardedById);
        map.put("created_at", createdAt);
        map.put("original_sender_name", originalSenderName);
        return map;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Message getOriginalMessage() { return originalMessage; }
    public void setOriginalMessage(Message originalMessage) { this.originalMessage = originalMessage; }
    public Long getForwardedMessageId() { return forwardedMessageId; }
    public void setForwardedMessageId(Long forwardedMessageId) { this.forwardedMessageId = forwardedMessageId; }
    public Long getForwardedById() { return forwardedById; }
    public void setForwardedById(Long forwardedById) { this.forwardedById = forwardedById; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    public String getOriginalSenderName() { return originalSenderName; }
    public void setOriginalSenderName(String originalSenderName) { this.originalSenderName = originalSenderName; }
}
