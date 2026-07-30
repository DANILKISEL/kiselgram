package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.util.HashMap;
import java.util.Map;

@Entity
@Table(name = "story_privacy")
public class StoryPrivacy {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "story_id", nullable = false)
    private Story story;

    @Column(name = "privacy_type", length = 20)
    private String privacyType;

    @Column(name = "allowed_user_id")
    private Long allowedUserId;

    public StoryPrivacy() {}

    public StoryPrivacy(Long id, Story story, String privacyType, Long allowedUserId) {
        this.id = id;
        this.story = story;
        this.privacyType = privacyType;
        this.allowedUserId = allowedUserId;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("id", id);
        map.put("story_id", story != null ? story.getId() : null);
        map.put("privacy_type", privacyType);
        map.put("allowed_user_id", allowedUserId);
        return map;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Story getStory() { return story; }
    public void setStory(Story story) { this.story = story; }
    public String getPrivacyType() { return privacyType; }
    public void setPrivacyType(String privacyType) { this.privacyType = privacyType; }
    public Long getAllowedUserId() { return allowedUserId; }
    public void setAllowedUserId(Long allowedUserId) { this.allowedUserId = allowedUserId; }
}
