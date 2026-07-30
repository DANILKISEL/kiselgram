package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Entity
@Table(name = "video_call_participants")
public class VideoCallParticipant {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "video_call_id", nullable = false)
    private VideoCall videoCall;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(name = "joined_at")
    private LocalDateTime joinedAt;

    @Column(name = "left_at")
    private LocalDateTime leftAt;

    @Column(name = "is_muted")
    private boolean isMuted;

    @Column(name = "is_video_on")
    private boolean isVideoOn;

    public VideoCallParticipant() {
        this.joinedAt = LocalDateTime.now();
        this.isMuted = false;
        this.isVideoOn = true;
    }

    public VideoCallParticipant(Long id, VideoCall videoCall, Long userId, LocalDateTime joinedAt,
                                LocalDateTime leftAt, boolean isMuted, boolean isVideoOn) {
        this.id = id;
        this.videoCall = videoCall;
        this.userId = userId;
        this.joinedAt = joinedAt;
        this.leftAt = leftAt;
        this.isMuted = isMuted;
        this.isVideoOn = isVideoOn;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("id", id);
        map.put("video_call_id", videoCall != null ? videoCall.getId() : null);
        map.put("user_id", userId);
        map.put("joined_at", joinedAt);
        map.put("left_at", leftAt);
        map.put("is_muted", isMuted);
        map.put("is_video_on", isVideoOn);
        return map;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public VideoCall getVideoCall() { return videoCall; }
    public void setVideoCall(VideoCall videoCall) { this.videoCall = videoCall; }
    public Long getUserId() { return userId; }
    public void setUserId(Long userId) { this.userId = userId; }
    public LocalDateTime getJoinedAt() { return joinedAt; }
    public void setJoinedAt(LocalDateTime joinedAt) { this.joinedAt = joinedAt; }
    public LocalDateTime getLeftAt() { return leftAt; }
    public void setLeftAt(LocalDateTime leftAt) { this.leftAt = leftAt; }
    public boolean isMuted() { return isMuted; }
    public void setMuted(boolean muted) { isMuted = muted; }
    public boolean isVideoOn() { return isVideoOn; }
    public void setVideoOn(boolean videoOn) { isVideoOn = videoOn; }
}
