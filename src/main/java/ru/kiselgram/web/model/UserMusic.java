package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Entity
@Table(name = "user_music")
public class UserMusic {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(length = 200)
    private String title;

    @Column(length = 200)
    private String artist;

    @Column(name = "file_path", length = 500)
    private String filePath;

    @Column(name = "file_size")
    private Integer fileSize;

    @Column(length = 50)
    private String duration;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    public UserMusic() {
        this.createdAt = LocalDateTime.now();
    }

    public UserMusic(Long id, Long userId, String title, String artist, String filePath,
                     Integer fileSize, String duration, LocalDateTime createdAt) {
        this.id = id;
        this.userId = userId;
        this.title = title;
        this.artist = artist;
        this.filePath = filePath;
        this.fileSize = fileSize;
        this.duration = duration;
        this.createdAt = createdAt;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("id", id);
        map.put("user_id", userId);
        map.put("title", title);
        map.put("artist", artist);
        map.put("file_path", filePath);
        map.put("file_size", fileSize);
        map.put("duration", duration);
        map.put("created_at", createdAt);
        return map;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getUserId() { return userId; }
    public void setUserId(Long userId) { this.userId = userId; }
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public String getArtist() { return artist; }
    public void setArtist(String artist) { this.artist = artist; }
    public String getFilePath() { return filePath; }
    public void setFilePath(String filePath) { this.filePath = filePath; }
    public Integer getFileSize() { return fileSize; }
    public void setFileSize(Integer fileSize) { this.fileSize = fileSize; }
    public String getDuration() { return duration; }
    public void setDuration(String duration) { this.duration = duration; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
