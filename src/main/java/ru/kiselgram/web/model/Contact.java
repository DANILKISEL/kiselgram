package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Entity
@Table(name = "contacts",
       uniqueConstraints = @UniqueConstraint(columnNames = {"user_id", "contact_id"}))
public class Contact {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @ManyToOne
    @JoinColumn(name = "contact_id", nullable = false)
    private User contactUser;

    @Column(name = "custom_name", length = 100)
    private String customName;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    public Contact() {
        this.createdAt = LocalDateTime.now();
    }

    public Contact(Long id, User user, User contactUser, String customName, LocalDateTime createdAt) {
        this.id = id;
        this.user = user;
        this.contactUser = contactUser;
        this.customName = customName;
        this.createdAt = createdAt;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("id", id);
        map.put("user_id", user != null ? user.getId() : null);
        map.put("contact_id", contactUser != null ? contactUser.getId() : null);
        map.put("custom_name", customName);
        map.put("created_at", createdAt);
        return map;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public User getUser() { return user; }
    public void setUser(User user) { this.user = user; }
    public User getContactUser() { return contactUser; }
    public void setContactUser(User contactUser) { this.contactUser = contactUser; }
    public String getCustomName() { return customName; }
    public void setCustomName(String customName) { this.customName = customName; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
