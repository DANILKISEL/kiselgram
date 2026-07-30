package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

@Entity
@Table(name = "video_calls")
public class VideoCall {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "call_id")
    private Long callId;

    @Column(name = "room_name", length = 100)
    private String roomName;

    @Column(name = "is_active")
    private boolean isActive;

    @Column(name = "started_at")
    private LocalDateTime startedAt;

    @Column(name = "ended_at")
    private LocalDateTime endedAt;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @OneToMany(mappedBy = "videoCall")
    private Set<VideoCallParticipant> participants = new HashSet<>();

    public VideoCall() {
        this.createdAt = LocalDateTime.now();
        this.isActive = true;
    }

    public VideoCall(Long id, Long callId, String roomName, boolean isActive,
                     LocalDateTime startedAt, LocalDateTime endedAt, LocalDateTime createdAt) {
        this.id = id;
        this.callId = callId;
        this.roomName = roomName;
        this.isActive = isActive;
        this.startedAt = startedAt;
        this.endedAt = endedAt;
        this.createdAt = createdAt;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("id", id);
        map.put("call_id", callId);
        map.put("room_name", roomName);
        map.put("is_active", isActive);
        map.put("started_at", startedAt);
        map.put("ended_at", endedAt);
        map.put("created_at", createdAt);
        return map;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getCallId() { return callId; }
    public void setCallId(Long callId) { this.callId = callId; }
    public String getRoomName() { return roomName; }
    public void setRoomName(String roomName) { this.roomName = roomName; }
    public boolean isActive() { return isActive; }
    public void setActive(boolean active) { isActive = active; }
    public LocalDateTime getStartedAt() { return startedAt; }
    public void setStartedAt(LocalDateTime startedAt) { this.startedAt = startedAt; }
    public LocalDateTime getEndedAt() { return endedAt; }
    public void setEndedAt(LocalDateTime endedAt) { this.endedAt = endedAt; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    public Set<VideoCallParticipant> getParticipants() { return participants; }
    public void setParticipants(Set<VideoCallParticipant> participants) { this.participants = participants; }
}
