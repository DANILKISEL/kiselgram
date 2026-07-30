package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.util.HashMap;
import java.util.Map;

@Entity
@Table(name = "story_allowed_users",
       uniqueConstraints = @UniqueConstraint(columnNames = {"story_id", "user_id"}))
public class StoryAllowedUser {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "story_id", nullable = false)
    private Story story;

    @ManyToOne
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    public StoryAllowedUser() {}

    public StoryAllowedUser(Long id, Story story, User user) {
        this.id = id;
        this.story = story;
        this.user = user;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("id", id);
        map.put("story_id", story != null ? story.getId() : null);
        map.put("user_id", user != null ? user.getId() : null);
        return map;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Story getStory() { return story; }
    public void setStory(Story story) { this.story = story; }
    public User getUser() { return user; }
    public void setUser(User user) { this.user = user; }
}
