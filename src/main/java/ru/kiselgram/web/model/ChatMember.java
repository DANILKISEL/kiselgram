package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Entity
@Table(name = "chat_members",
       uniqueConstraints = @UniqueConstraint(columnNames = {"chat_id", "user_id"}))
public class ChatMember {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "chat_id", nullable = false)
    private Chat chat;

    @ManyToOne
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(length = 20)
    private String role;

    @Column(name = "joined_at", nullable = false, updatable = false)
    private LocalDateTime joinedAt;

    public ChatMember() {
        this.joinedAt = LocalDateTime.now();
        this.role = "member";
    }

    public ChatMember(Long id, Chat chat, User user, String role, LocalDateTime joinedAt) {
        this.id = id;
        this.chat = chat;
        this.user = user;
        this.role = role;
        this.joinedAt = joinedAt;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("id", id);
        map.put("chat_id", chat != null ? chat.getId() : null);
        map.put("user_id", user != null ? user.getId() : null);
        map.put("role", role);
        map.put("joined_at", joinedAt);
        return map;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Chat getChat() { return chat; }
    public void setChat(Chat chat) { this.chat = chat; }
    public User getUser() { return user; }
    public void setUser(User user) { this.user = user; }
    public String getRole() { return role; }
    public void setRole(String role) { this.role = role; }
    public LocalDateTime getJoinedAt() { return joinedAt; }
    public void setJoinedAt(LocalDateTime joinedAt) { this.joinedAt = joinedAt; }
}
