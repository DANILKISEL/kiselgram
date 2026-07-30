package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Entity
@Table(name = "calls")
public class Call {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "caller_id", nullable = false)
    private Long callerId;

    @Column(name = "receiver_id", nullable = false)
    private Long receiverId;

    @Column(length = 20)
    private String status;

    @Column(name = "call_type", length = 20)
    private String callType;

    @Column(name = "started_at")
    private LocalDateTime startedAt;

    @Column(name = "ended_at")
    private LocalDateTime endedAt;

    @Column(name = "duration")
    private Integer duration;

    @Column(name = "is_video")
    private boolean isVideo;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    public Call() {
        this.createdAt = LocalDateTime.now();
    }

    public Call(Long id, Long callerId, Long receiverId, String status, String callType,
                LocalDateTime startedAt, LocalDateTime endedAt, Integer duration,
                boolean isVideo, LocalDateTime createdAt) {
        this.id = id;
        this.callerId = callerId;
        this.receiverId = receiverId;
        this.status = status;
        this.callType = callType;
        this.startedAt = startedAt;
        this.endedAt = endedAt;
        this.duration = duration;
        this.isVideo = isVideo;
        this.createdAt = createdAt;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("id", id);
        map.put("caller_id", callerId);
        map.put("receiver_id", receiverId);
        map.put("status", status);
        map.put("call_type", callType);
        map.put("started_at", startedAt);
        map.put("ended_at", endedAt);
        map.put("duration", duration);
        map.put("is_video", isVideo);
        map.put("created_at", createdAt);
        return map;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getCallerId() { return callerId; }
    public void setCallerId(Long callerId) { this.callerId = callerId; }
    public Long getReceiverId() { return receiverId; }
    public void setReceiverId(Long receiverId) { this.receiverId = receiverId; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public String getCallType() { return callType; }
    public void setCallType(String callType) { this.callType = callType; }
    public LocalDateTime getStartedAt() { return startedAt; }
    public void setStartedAt(LocalDateTime startedAt) { this.startedAt = startedAt; }
    public LocalDateTime getEndedAt() { return endedAt; }
    public void setEndedAt(LocalDateTime endedAt) { this.endedAt = endedAt; }
    public Integer getDuration() { return duration; }
    public void setDuration(Integer duration) { this.duration = duration; }
    public boolean isVideo() { return isVideo; }
    public void setVideo(boolean video) { isVideo = video; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
