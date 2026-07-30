package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Entity
@Table(name = "favorites")
public class Favorite {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(name = "favorite_type", length = 20)
    private String favoriteType;

    @Column(name = "favorite_id")
    private Long favoriteId;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    public Favorite() {
        this.createdAt = LocalDateTime.now();
    }

    public Favorite(Long id, User user, String favoriteType, Long favoriteId, LocalDateTime createdAt) {
        this.id = id;
        this.user = user;
        this.favoriteType = favoriteType;
        this.favoriteId = favoriteId;
        this.createdAt = createdAt;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("id", id);
        map.put("user_id", user != null ? user.getId() : null);
        map.put("favorite_type", favoriteType);
        map.put("favorite_id", favoriteId);
        map.put("created_at", createdAt);
        return map;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public User getUser() { return user; }
    public void setUser(User user) { this.user = user; }
    public String getFavoriteType() { return favoriteType; }
    public void setFavoriteType(String favoriteType) { this.favoriteType = favoriteType; }
    public Long getFavoriteId() { return favoriteId; }
    public void setFavoriteId(Long favoriteId) { this.favoriteId = favoriteId; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
