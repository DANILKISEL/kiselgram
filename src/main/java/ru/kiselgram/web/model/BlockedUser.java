package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Entity
@Table(name = "blocked_users",
       uniqueConstraints = @UniqueConstraint(columnNames = {"user_id", "blocked_user_id"}))
public class BlockedUser {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @ManyToOne
    @JoinColumn(name = "blocked_user_id", nullable = false)
    private User blockedUser;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    public BlockedUser() {
        this.createdAt = LocalDateTime.now();
    }

    public BlockedUser(Long id, User user, User blockedUser, LocalDateTime createdAt) {
        this.id = id;
        this.user = user;
        this.blockedUser = blockedUser;
        this.createdAt = createdAt;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("id", id);
        map.put("user_id", user != null ? user.getId() : null);
        map.put("blocked_user_id", blockedUser != null ? blockedUser.getId() : null);
        map.put("created_at", createdAt);
        return map;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public User getUser() { return user; }
    public void setUser(User user) { this.user = user; }
    public User getBlockedUser() { return blockedUser; }
    public void setBlockedUser(User blockedUser) { this.blockedUser = blockedUser; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
