package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Entity
@Table(name = "invite_links")
public class InviteLink {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "chat_id", nullable = false)
    private Long chatId;

    @Column(nullable = false, unique = true, length = 100)
    private String code;

    @Column(name = "created_by", nullable = false)
    private Long createdBy;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "expires_at")
    private LocalDateTime expiresAt;

    @Column(name = "max_uses")
    private Integer maxUses;

    @Column(name = "use_count")
    private Integer useCount;

    @Column(name = "is_revoked")
    private boolean isRevoked;

    public InviteLink() {
        this.createdAt = LocalDateTime.now();
        this.useCount = 0;
        this.isRevoked = false;
    }

    public InviteLink(Long id, Long chatId, String code, Long createdBy, LocalDateTime createdAt,
                      LocalDateTime expiresAt, Integer maxUses, Integer useCount, boolean isRevoked) {
        this.id = id;
        this.chatId = chatId;
        this.code = code;
        this.createdBy = createdBy;
        this.createdAt = createdAt;
        this.expiresAt = expiresAt;
        this.maxUses = maxUses;
        this.useCount = useCount;
        this.isRevoked = isRevoked;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("id", id);
        map.put("chat_id", chatId);
        map.put("code", code);
        map.put("created_by", createdBy);
        map.put("created_at", createdAt);
        map.put("expires_at", expiresAt);
        map.put("max_uses", maxUses);
        map.put("use_count", useCount);
        map.put("is_revoked", isRevoked);
        return map;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getChatId() { return chatId; }
    public void setChatId(Long chatId) { this.chatId = chatId; }
    public String getCode() { return code; }
    public void setCode(String code) { this.code = code; }
    public Long getCreatedBy() { return createdBy; }
    public void setCreatedBy(Long createdBy) { this.createdBy = createdBy; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    public LocalDateTime getExpiresAt() { return expiresAt; }
    public void setExpiresAt(LocalDateTime expiresAt) { this.expiresAt = expiresAt; }
    public Integer getMaxUses() { return maxUses; }
    public void setMaxUses(Integer maxUses) { this.maxUses = maxUses; }
    public Integer getUseCount() { return useCount; }
    public void setUseCount(Integer useCount) { this.useCount = useCount; }
    public boolean isRevoked() { return isRevoked; }
    public void setRevoked(boolean revoked) { isRevoked = revoked; }
}
