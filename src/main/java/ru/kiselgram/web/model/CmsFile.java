package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Entity
@Table(name = "files")
public class CmsFile {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "file_type", length = 20)
    private String fileType;

    @Column(name = "file_name", length = 255)
    private String fileName;

    @Column(name = "file_path", length = 500)
    private String filePath;

    @Column(name = "thumbnail_path", length = 500)
    private String thumbnailPath;

    @Column(name = "preview_size", length = 20)
    private String previewSize;

    @Column(name = "file_size")
    private Integer fileSize;

    @Column(name = "uploader_id")
    private Long uploaderId;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    public CmsFile() {
        this.createdAt = LocalDateTime.now();
    }

    public CmsFile(Long id, String fileType, String fileName, String filePath,
                   String thumbnailPath, String previewSize, Integer fileSize,
                   Long uploaderId, LocalDateTime createdAt) {
        this.id = id;
        this.fileType = fileType;
        this.fileName = fileName;
        this.filePath = filePath;
        this.thumbnailPath = thumbnailPath;
        this.previewSize = previewSize;
        this.fileSize = fileSize;
        this.uploaderId = uploaderId;
        this.createdAt = createdAt;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("id", id);
        map.put("file_type", fileType);
        map.put("file_name", fileName);
        map.put("file_path", filePath);
        map.put("thumbnail_path", thumbnailPath);
        map.put("preview_size", previewSize);
        map.put("file_size", fileSize);
        map.put("uploader_id", uploaderId);
        map.put("created_at", createdAt);
        return map;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getFileType() { return fileType; }
    public void setFileType(String fileType) { this.fileType = fileType; }
    public String getFileName() { return fileName; }
    public void setFileName(String fileName) { this.fileName = fileName; }
    public String getFilePath() { return filePath; }
    public void setFilePath(String filePath) { this.filePath = filePath; }
    public String getThumbnailPath() { return thumbnailPath; }
    public void setThumbnailPath(String thumbnailPath) { this.thumbnailPath = thumbnailPath; }
    public String getPreviewSize() { return previewSize; }
    public void setPreviewSize(String previewSize) { this.previewSize = previewSize; }
    public Integer getFileSize() { return fileSize; }
    public void setFileSize(Integer fileSize) { this.fileSize = fileSize; }
    public Long getUploaderId() { return uploaderId; }
    public void setUploaderId(Long uploaderId) { this.uploaderId = uploaderId; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
