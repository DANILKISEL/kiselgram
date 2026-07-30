package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Entity
@Table(name = "preloaded_avatars")
public class PreloadedAvatar {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "avatar_url", length = 500)
    private String avatarUrl;

    @Column(length = 20)
    private String color;

    @Column(name = "is_active")
    private boolean isActive;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    public PreloadedAvatar() {
        this.createdAt = LocalDateTime.now();
        this.isActive = true;
    }

    public PreloadedAvatar(Long id, String avatarUrl, String color, boolean isActive, LocalDateTime createdAt) {
        this.id = id;
        this.avatarUrl = avatarUrl;
        this.color = color;
        this.isActive = isActive;
        this.createdAt = createdAt;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("id", id);
        map.put("avatar_url", avatarUrl);
        map.put("color", color);
        map.put("is_active", isActive);
        map.put("created_at", createdAt);
        return map;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getAvatarUrl() { return avatarUrl; }
    public void setAvatarUrl(String avatarUrl) { this.avatarUrl = avatarUrl; }
    public String getColor() { return color; }
    public void setColor(String color) { this.color = color; }
    public boolean isActive() { return isActive; }
    public void setActive(boolean active) { isActive = active; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
