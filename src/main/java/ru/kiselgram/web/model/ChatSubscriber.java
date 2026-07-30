package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Entity
@Table(name = "chat_subscribers",
       uniqueConstraints = @UniqueConstraint(columnNames = {"chat_id", "user_id"}))
public class ChatSubscriber {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "chat_id", nullable = false)
    private Chat chat;

    @ManyToOne
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(name = "subscribed_at", nullable = false, updatable = false)
    private LocalDateTime subscribedAt;

    public ChatSubscriber() {
        this.subscribedAt = LocalDateTime.now();
    }

    public ChatSubscriber(Long id, Chat chat, User user, LocalDateTime subscribedAt) {
        this.id = id;
        this.chat = chat;
        this.user = user;
        this.subscribedAt = subscribedAt;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("id", id);
        map.put("chat_id", chat != null ? chat.getId() : null);
        map.put("user_id", user != null ? user.getId() : null);
        map.put("subscribed_at", subscribedAt);
        return map;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Chat getChat() { return chat; }
    public void setChat(Chat chat) { this.chat = chat; }
    public User getUser() { return user; }
    public void setUser(User user) { this.user = user; }
    public LocalDateTime getSubscribedAt() { return subscribedAt; }
    public void setSubscribedAt(LocalDateTime subscribedAt) { this.subscribedAt = subscribedAt; }
}
