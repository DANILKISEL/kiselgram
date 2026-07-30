package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Entity
@Table(name = "reports")
public class Report {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(name = "reported_user_id")
    private Long reportedUserId;

    @Column(name = "reported_message_id")
    private Long reportedMessageId;

    @Column(length = 50)
    private String reason;

    @Column(columnDefinition = "TEXT")
    private String description;

    @Column(length = 20)
    private String status;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "resolved_at")
    private LocalDateTime resolvedAt;

    @Column(name = "resolved_by")
    private Long resolvedBy;

    public Report() {
        this.createdAt = LocalDateTime.now();
        this.status = "pending";
    }

    public Report(Long id, User user, Long reportedUserId, Long reportedMessageId,
                  String reason, String description, String status, LocalDateTime createdAt,
                  LocalDateTime resolvedAt, Long resolvedBy) {
        this.id = id;
        this.user = user;
        this.reportedUserId = reportedUserId;
        this.reportedMessageId = reportedMessageId;
        this.reason = reason;
        this.description = description;
        this.status = status;
        this.createdAt = createdAt;
        this.resolvedAt = resolvedAt;
        this.resolvedBy = resolvedBy;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("id", id);
        map.put("user_id", user != null ? user.getId() : null);
        map.put("reported_user_id", reportedUserId);
        map.put("reported_message_id", reportedMessageId);
        map.put("reason", reason);
        map.put("description", description);
        map.put("status", status);
        map.put("created_at", createdAt);
        map.put("resolved_at", resolvedAt);
        map.put("resolved_by", resolvedBy);
        return map;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public User getUser() { return user; }
    public void setUser(User user) { this.user = user; }
    public Long getReportedUserId() { return reportedUserId; }
    public void setReportedUserId(Long reportedUserId) { this.reportedUserId = reportedUserId; }
    public Long getReportedMessageId() { return reportedMessageId; }
    public void setReportedMessageId(Long reportedMessageId) { this.reportedMessageId = reportedMessageId; }
    public String getReason() { return reason; }
    public void setReason(String reason) { this.reason = reason; }
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    public LocalDateTime getResolvedAt() { return resolvedAt; }
    public void setResolvedAt(LocalDateTime resolvedAt) { this.resolvedAt = resolvedAt; }
    public Long getResolvedBy() { return resolvedBy; }
    public void setResolvedBy(Long resolvedBy) { this.resolvedBy = resolvedBy; }
}
