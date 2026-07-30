package ru.kiselgram.web.util;

import ru.kiselgram.web.config.AppConfig;
import ru.kiselgram.web.config.HibernateConfig;
import ru.kiselgram.web.model.*;
import com.nimbusds.jose.JWSVerifier;
import com.nimbusds.jose.crypto.MACVerifier;
import com.nimbusds.jwt.JWTClaimsSet;
import com.nimbusds.jwt.SignedJWT;
import org.hibernate.Session;
import org.hibernate.query.NativeQuery;
import org.hibernate.query.Query;

import java.security.MessageDigest;
import java.security.SecureRandom;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

public final class Helpers {

    private static final SecureRandom RNG = new SecureRandom();
    private static final DateTimeFormatter TIMESTAMP_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    private static final Set<String> IMAGE_EXTENSIONS = Set.of("jpg", "jpeg", "png", "gif", "bmp", "webp");
    private static final Set<String> DOCUMENT_EXTENSIONS = Set.of("pdf", "doc", "docx", "txt", "rtf", "odt");
    private static final Set<String> VIDEO_EXTENSIONS = Set.of("mp4", "avi", "mov", "mkv", "webm");
    private static final Set<String> AUDIO_EXTENSIONS = Set.of("mp3", "wav", "ogg", "m4a", "flac");
    private static final Set<String> ARCHIVE_EXTENSIONS = Set.of("zip", "rar", "7z", "tar", "gz");

    private Helpers() {}

    public static String hashPassword(String password) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(password.getBytes("UTF-8"));
            return Base64.getEncoder().encodeToString(hash);
        } catch (Exception e) {
            throw new RuntimeException("Failed to hash password", e);
        }
    }

    public static boolean checkPassword(String password, String hash) {
        return hashPassword(password).equals(hash);
    }

    public static User getUserFromToken(String authorizationHeader) {
        if (authorizationHeader == null || !authorizationHeader.startsWith("Bearer ")) {
            return null;
        }
        String token = authorizationHeader.substring(7);
        try {
            String secret = AppConfig.getInstance().getApp().getSecretKey();
            if (secret.length() < 32) {
                StringBuilder sb = new StringBuilder(secret);
                while (sb.length() < 32) {
                    sb.append("0");
                }
                secret = sb.toString();
            }

            SignedJWT signedJWT = SignedJWT.parse(token);
            JWSVerifier verifier = new MACVerifier(secret.getBytes());
            if (!signedJWT.verify(verifier)) {
                return null;
            }

            JWTClaimsSet claims = signedJWT.getJWTClaimsSet();
            if (claims.getExpirationTime() != null && claims.getExpirationTime().before(new Date())) {
                return null;
            }

            Long userId = claims.getLongClaim("user_id");
            if (userId == null) {
                String subject = claims.getSubject();
                if (subject == null) return null;
                try {
                    userId = Long.parseLong(subject);
                } catch (NumberFormatException e) {
                    return null;
                }
            }

            Session session = HibernateConfig.getInstance().getSession();
            User user = session.get(User.class, userId);
            return user;
        } catch (Exception e) {
            return null;
        }
    }

    public static String generateInviteLink() {
        byte[] token = new byte[16];
        RNG.nextBytes(token);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(token);
    }

    public static String formatFileSize(long bytes) {
        if (bytes == 0) return "0 B";
        String[] units = {"B", "KB", "MB", "GB", "TB"};
        int unitIndex = 0;
        double size = bytes;
        while (size >= 1024 && unitIndex < units.length - 1) {
            size /= 1024.0;
            unitIndex++;
        }
        if (unitIndex == 0) {
            return String.format("%d %s", (long) size, units[unitIndex]);
        }
        return String.format("%.1f %s", size, units[unitIndex]);
    }

    public static String formatTimestamp(LocalDateTime timestamp) {
        if (timestamp == null) return "";
        return timestamp.format(TIMESTAMP_FORMATTER);
    }

    public static boolean allowedFile(String filename, String fileType) {
        if (filename == null || filename.isEmpty()) return false;
        String ext = getExtension(filename);
        if (ext.isEmpty()) return false;

        AppConfig.UploadsSection uploads = AppConfig.getInstance().getUploads();

        return switch (fileType) {
            case "image" -> uploads.getAllowedImages().contains(ext);
            case "document" -> uploads.getAllowedDocuments().contains(ext);
            case "video" -> uploads.getAllowedVideos().contains(ext);
            default -> uploads.getAllowedImages().contains(ext)
                    || uploads.getAllowedDocuments().contains(ext)
                    || uploads.getAllowedVideos().contains(ext);
        };
    }

    public static String getFileType(String filename) {
        if (filename == null || filename.isEmpty()) return "unknown";
        String ext = getExtension(filename);
        if (ext.isEmpty()) return "unknown";

        if (IMAGE_EXTENSIONS.contains(ext)) return "image";
        if (DOCUMENT_EXTENSIONS.contains(ext)) return "document";
        if (VIDEO_EXTENSIONS.contains(ext)) return "video";
        if (AUDIO_EXTENSIONS.contains(ext)) return "audio";
        if (ARCHIVE_EXTENSIONS.contains(ext)) return "archive";
        return "unknown";
    }

    public static Map<String, Object> messageToDict(Message message) {
        Map<String, Object> dict = new LinkedHashMap<>();
        dict.put("id", message.getId());
        dict.put("content", message.getContent());
        Session session = HibernateConfig.getInstance().getSession();
        User sender = session.get(User.class, message.getSenderId());
        dict.put("sender", userToDict(sender));
        if (message.getReceiverId() != null) {
            User receiver = session.get(User.class, message.getReceiverId());
            dict.put("receiver", userToDict(receiver));
        }
        dict.put("timestamp", formatTimestamp(message.getTimestamp()));
        dict.put("is_read", message.isRead());
        dict.put("has_attachment", message.isHasAttachment());
        dict.put("file_type", message.getFileType());
        dict.put("file_name", message.getFileName());
        dict.put("file_path", message.getFilePath());
        dict.put("file_size", message.getFileSize());
        dict.put("thumbnail_path", message.getThumbnailPath());
        if (message.getChatId() != null) {
            Chat chat = session.get(Chat.class, message.getChatId());
            if (chat != null) {
                dict.put("chat_id", chat.getId());
                dict.put("chat_name", chat.getName());
            }
        }
        return dict;
    }

    public static Map<String, Object> userToDict(User user) {
        Map<String, Object> dict = new LinkedHashMap<>();
        dict.put("id", user.getId());
        dict.put("username", user.getUsername());
        if (user.getTelegramUsername() != null) {
            dict.put("telegram_username", user.getTelegramUsername());
        }
        dict.put("created_at", formatTimestamp(user.getCreatedAt()));
        return dict;
    }

    public static boolean hasActiveStory(Long userId) {
        try {
            Session session = HibernateConfig.getInstance().getSession();
            NativeQuery<Long> query = session.createNativeQuery(
                    "SELECT COUNT(*) FROM stories WHERE user_id = :uid AND created_at >= :cutoff",
                    Long.class);
            query.setParameter("uid", userId);
            query.setParameter("cutoff", LocalDateTime.now().minusHours(24));
            Long count = query.uniqueResult();
            return count != null && count > 0;
        } catch (Exception e) {
            return false;
        }
    }

    public static Set<Long> getBlockedUserIds(Long userId) {
        try {
            Session session = HibernateConfig.getInstance().getSession();
            NativeQuery<Long> query = session.createNativeQuery(
                    "SELECT blocked_id FROM blocked_users WHERE user_id = :uid",
                    Long.class);
            query.setParameter("uid", userId);
            return new HashSet<>(query.list());
        } catch (Exception e) {
            return Collections.emptySet();
        }
    }

    private static String getExtension(String filename) {
        int dot = filename.lastIndexOf('.');
        if (dot <= 0 || dot >= filename.length() - 1) return "";
        return filename.substring(dot + 1).toLowerCase();
    }
}
