package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Entity
@Table(name = "poll_votes")
public class PollVote {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "poll_id", nullable = false)
    private Poll poll;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(name = "option_id")
    private Integer optionId;

    @Column(name = "voted_at", nullable = false, updatable = false)
    private LocalDateTime votedAt;

    public PollVote() {
        this.votedAt = LocalDateTime.now();
    }

    public PollVote(Long id, Poll poll, Long userId, Integer optionId, LocalDateTime votedAt) {
        this.id = id;
        this.poll = poll;
        this.userId = userId;
        this.optionId = optionId;
        this.votedAt = votedAt;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("id", id);
        map.put("poll_id", poll != null ? poll.getId() : null);
        map.put("user_id", userId);
        map.put("option_id", optionId);
        map.put("voted_at", votedAt);
        return map;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Poll getPoll() { return poll; }
    public void setPoll(Poll poll) { this.poll = poll; }
    public Long getUserId() { return userId; }
    public void setUserId(Long userId) { this.userId = userId; }
    public Integer getOptionId() { return optionId; }
    public void setOptionId(Integer optionId) { this.optionId = optionId; }
    public LocalDateTime getVotedAt() { return votedAt; }
    public void setVotedAt(LocalDateTime votedAt) { this.votedAt = votedAt; }
}
