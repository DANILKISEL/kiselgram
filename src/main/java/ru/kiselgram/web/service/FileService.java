package ru.kiselgram.web.service;

import ru.kiselgram.web.model.CmsFile;
import ru.kiselgram.web.model.User;
import org.hibernate.Session;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.LocalDateTime;
import java.util.Map;
import java.util.UUID;

import static ru.kiselgram.web.config.HibernateConfig.getInstance;

public class FileService {

    private static final String UPLOAD_DIR = "uploads";

    public FileService() {
        File dir = new File(UPLOAD_DIR);
        if (!dir.exists()) dir.mkdirs();
    }

    public Map<String, Object> upload(User user, byte[] data, String originalName, String mimeType) {
        if (user == null) return Map.of("error", "Not authenticated");
        if (data == null || data.length == 0) return Map.of("error", "No data");
        if (data.length > 100 * 1024 * 1024) return Map.of("error", "File too large");

        String ext = "";
        if (originalName != null && originalName.contains("."))
            ext = originalName.substring(originalName.lastIndexOf('.'));
        String storedName = UUID.randomUUID().toString() + ext;
        String subdir = storedName.substring(0, 2);
        Path dirPath = Path.of(UPLOAD_DIR, subdir);
        Path filePath = dirPath.resolve(storedName);

        try {
            Files.createDirectories(dirPath);
            Files.write(filePath, data);
        } catch (IOException e) {
            return Map.of("error", "Failed to save file: " + e.getMessage());
        }

        CmsFile cmsFile = new CmsFile();
        cmsFile.setFileName(originalName != null ? originalName : "unnamed");
        cmsFile.setFileType(mimeType != null ? mimeType : "application/octet-stream");
        cmsFile.setFilePath(subdir + "/" + storedName);
        cmsFile.setFileSize((int) data.length);
        cmsFile.setUploaderId(user.getId());
        cmsFile.setCreatedAt(LocalDateTime.now());

        try (Session s = getInstance().getSessionFactory().openSession()) {
            s.beginTransaction();
            s.persist(cmsFile);
            s.getTransaction().commit();
        }

        return cmsFile.toMap();
    }

    public CmsFile getFile(long fileId) {
        try (Session s = getInstance().getSessionFactory().openSession()) {
            return s.get(CmsFile.class, fileId);
        }
    }

    public Path getFilePath(CmsFile file) {
        return Path.of(UPLOAD_DIR, file.getFilePath());
    }

    public Map<String, Object> deleteFile(User user, long fileId) {
        if (user == null) return Map.of("error", "Not authenticated");
        try (Session s = getInstance().getSessionFactory().openSession()) {
            s.beginTransaction();
            CmsFile file = s.get(CmsFile.class, fileId);
            if (file == null) return Map.of("error", "File not found");
            if (file.getUploaderId() != user.getId() && !user.isAdmin())
                return Map.of("error", "Forbidden");
            Path p = Path.of(UPLOAD_DIR, file.getFilePath());
            try { Files.deleteIfExists(p); } catch (IOException ignored) {}
            s.remove(file);
            s.getTransaction().commit();
        }
        return Map.of("message", "File deleted");
    }
}
