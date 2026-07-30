package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

@Entity
@Table(name = "stories")
public class Story {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(name = "media_path", nullable = false, length = 500)
    private String mediaPath;

    @Column(name = "media_type", length = 20)
    private String mediaType;

    @Column(columnDefinition = "TEXT")
    private String caption;

    @Column(name = "music_path", length = 500)
    private String musicPath;

    @Column(name = "privacy_type", length = 20)
    private String privacyType;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @OneToMany(mappedBy = "story")
    private Set<StoryView> views = new HashSet<>();

    @OneToMany(mappedBy = "story")
    private Set<StoryLike> likes = new HashSet<>();

    @OneToMany(mappedBy = "story")
    private Set<StoryReaction> reactions = new HashSet<>();

    @OneToMany(mappedBy = "story")
    private Set<StoryPrivacy> privacySettings = new HashSet<>();

    @OneToMany(mappedBy = "story")
    private Set<StoryAllowedUser> allowedUsers = new HashSet<>();

    public Story() {
        this.createdAt = LocalDateTime.now();
    }

    public Story(Long id, User user, String mediaPath, String mediaType, String caption,
                 String musicPath, String privacyType, LocalDateTime createdAt) {
        this.id = id;
        this.user = user;
        this.mediaPath = mediaPath;
        this.mediaType = mediaType;
        this.caption = caption;
        this.musicPath = musicPath;
        this.privacyType = privacyType;
        this.createdAt = createdAt;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("id", id);
        map.put("user_id", user != null ? user.getId() : null);
        map.put("media_path", mediaPath);
        map.put("media_type", mediaType);
        map.put("caption", caption);
        map.put("music_path", musicPath);
        map.put("privacy_type", privacyType);
        map.put("created_at", createdAt);
        return map;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public User getUser() { return user; }
    public void setUser(User user) { this.user = user; }
    public String getMediaPath() { return mediaPath; }
    public void setMediaPath(String mediaPath) { this.mediaPath = mediaPath; }
    public String getMediaType() { return mediaType; }
    public void setMediaType(String mediaType) { this.mediaType = mediaType; }
    public String getCaption() { return caption; }
    public void setCaption(String caption) { this.caption = caption; }
    public String getMusicPath() { return musicPath; }
    public void setMusicPath(String musicPath) { this.musicPath = musicPath; }
    public String getPrivacyType() { return privacyType; }
    public void setPrivacyType(String privacyType) { this.privacyType = privacyType; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    public Set<StoryView> getViews() { return views; }
    public void setViews(Set<StoryView> views) { this.views = views; }
    public Set<StoryLike> getLikes() { return likes; }
    public void setLikes(Set<StoryLike> likes) { this.likes = likes; }
    public Set<StoryReaction> getReactions() { return reactions; }
    public void setReactions(Set<StoryReaction> reactions) { this.reactions = reactions; }
    public Set<StoryPrivacy> getPrivacySettings() { return privacySettings; }
    public void setPrivacySettings(Set<StoryPrivacy> privacySettings) { this.privacySettings = privacySettings; }
    public Set<StoryAllowedUser> getAllowedUsers() { return allowedUsers; }
    public void setAllowedUsers(Set<StoryAllowedUser> allowedUsers) { this.allowedUsers = allowedUsers; }
}
