package ru.kiselgram.web.config;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.toml.TomlFactory;
import ru.kiselgram.web.util.CryptoUtil;
import io.github.cdimascio.dotenv.Dotenv;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public final class AppConfig {

    public static final long PREMIUM_PRICE_MONTHLY = 300;
    public static final long PREMIUM_PRICE_YEARLY = 2990;
    public static final int PREMIUM_TRIAL_DAYS = 7;
    public static final long MAX_CONTENT_LENGTH = 100 * 1024 * 1024;
    public static final String UPLOAD_FOLDER = "uploads";
    public static final int SESSION_COOKIE_AGE = 86400;
    public static final boolean SESSION_COOKIE_SECURE = true;
    public static final boolean SESSION_COOKIE_HTTPONLY = true;
    public static final String SESSION_COOKIE_SAMESITE = "Lax";

    private static volatile AppConfig instance;

    private final AppSection app = new AppSection();
    private final AuthSection auth = new AuthSection();
    private final DatabaseSection database = new DatabaseSection();
    private final ServerSection server = new ServerSection();
    private final VideoSection video = new VideoSection();
    private final LoggingSection logging = new LoggingSection();
    private final TelegramSection telegram = new TelegramSection();
    private final UploadsSection uploads = new UploadsSection();
    private final FeaturesSection features = new FeaturesSection();
    private final MailSection mail = new MailSection();
    private final GoogleSection google = new GoogleSection();

    private AppConfig() {
        Dotenv dotenv = Dotenv.configure().ignoreIfMissing().load();
        loadTomlConfig(dotenv);
        applyEnvOverrides(dotenv);
    }

    public static AppConfig getInstance() {
        if (instance == null) {
            synchronized (AppConfig.class) {
                if (instance == null) {
                    instance = new AppConfig();
                }
            }
        }
        return instance;
    }

    private void loadTomlConfig(Dotenv dotenv) {
        String configPath = dotenv.get("CONFIG_PATH", "config/kis.toml");
        File tomlFile = new File(configPath);
        if (!tomlFile.exists()) {
            return;
        }
        try {
            ObjectMapper mapper = new ObjectMapper(new TomlFactory());
            JsonNode root = mapper.readTree(tomlFile);

            if (root.has("app")) {
                JsonNode n = root.get("app");
                app.name = getText(n, "name", app.name);
                app.version = getText(n, "version", app.version);
                app.debug = getBool(n, "debug", app.debug);
                app.host = getText(n, "host", app.host);
                app.port = getInt(n, "port", app.port);
                app.secretKey = getText(n, "secret_key", app.secretKey);
            }
            if (root.has("auth")) {
                JsonNode n = root.get("auth");
                auth.port = getInt(n, "port", auth.port);
            }
            if (root.has("database")) {
                JsonNode n = root.get("database");
                database.url = getText(n, "url", database.url);
                database.echo = getBool(n, "echo", database.echo);
            }
            if (root.has("server")) {
                JsonNode n = root.get("server");
                server.workers = getInt(n, "workers", server.workers);
                server.threaded = getBool(n, "threaded", server.threaded);
            }
            if (root.has("video")) {
                JsonNode n = root.get("video");
                video.enabled = getBool(n, "enabled", video.enabled);
                video.host = getText(n, "host", video.host);
                video.port = getInt(n, "port", video.port);
                video.quality = getInt(n, "quality", video.quality);
                video.maxSize = getLong(n, "max_size", video.maxSize);
            }
            if (root.has("logging")) {
                JsonNode n = root.get("logging");
                logging.level = getText(n, "level", logging.level);
                logging.format = getText(n, "format", logging.format);
                logging.file = getText(n, "file", logging.file);
                logging.maxSize = getLong(n, "max_size", logging.maxSize);
                logging.backupCount = getInt(n, "backup_count", logging.backupCount);
            }
            if (root.has("telegram")) {
                JsonNode n = root.get("telegram");
                telegram.botToken = getText(n, "bot_token", telegram.botToken);
                telegram.webhookUrl = getText(n, "webhook_url", telegram.webhookUrl);
            }
            if (root.has("uploads")) {
                JsonNode n = root.get("uploads");
                uploads.folder = getText(n, "folder", uploads.folder);
                uploads.maxSize = getLong(n, "max_size", uploads.maxSize);
                uploads.allowedImages = getStringList(n, "allowed_images", uploads.allowedImages);
                uploads.allowedDocuments = getStringList(n, "allowed_documents", uploads.allowedDocuments);
                uploads.allowedVideos = getStringList(n, "allowed_videos", uploads.allowedVideos);
            }
            if (root.has("features")) {
                JsonNode n = root.get("features");
                features.groups = getBool(n, "groups", features.groups);
                features.channels = getBool(n, "channels", features.channels);
                features.bots = getBool(n, "bots", features.bots);
                features.videoStreaming = getBool(n, "video_streaming", features.videoStreaming);
                features.fileSharing = getBool(n, "file_sharing", features.fileSharing);
                features.reactions = getBool(n, "reactions", features.reactions);
            }
            if (root.has("mail")) {
                JsonNode n = root.get("mail");
                mail.server = getText(n, "server", mail.server);
                mail.port = getInt(n, "port", mail.port);
                mail.username = getText(n, "username", mail.username);
                mail.password = getText(n, "password", mail.password);
                mail.senderName = getText(n, "sender_name", mail.senderName);
                mail.senderEmail = getText(n, "sender_email", mail.senderEmail);
            }
            if (root.has("google")) {
                JsonNode n = root.get("google");
                google.clientId = getText(n, "client_id", google.clientId);
                google.clientSecret = getText(n, "client_secret", google.clientSecret);
                google.redirectUri = getText(n, "redirect_uri", google.redirectUri);
            }
        } catch (IOException e) {
            System.err.println("Failed to load config/kis.toml: " + e.getMessage());
        }
    }

    private void applyEnvOverrides(Dotenv dotenv) {
        String val;
        val = dotenv.get("APP_SECRET_KEY");
        if (val != null) app.secretKey = val;
        val = dotenv.get("DATABASE_URL");
        if (val != null) database.url = val;
        val = dotenv.get("TELEGRAM_BOT_TOKEN");
        if (val != null) telegram.botToken = val;
        val = dotenv.get("TELEGRAM_WEBHOOK_URL");
        if (val != null) telegram.webhookUrl = val;
        val = dotenv.get("MAIL_USERNAME");
        if (val != null) mail.username = val;
        val = dotenv.get("MAIL_PASSWORD");
        if (val != null) mail.password = val;
        val = dotenv.get("GOOGLE_CLIENT_ID");
        if (val != null) google.clientId = val;
        val = dotenv.get("GOOGLE_CLIENT_SECRET");
        if (val != null) google.clientSecret = val;
        val = dotenv.get("MESSAGE_ENCRYPTION_KEY");
        if (val != null) CryptoUtil.ENCRYPTION_KEY = val;
    }

    private static String getText(JsonNode node, String field, String def) {
        JsonNode n = node.get(field);
        return n != null && !n.isNull() ? n.asText() : def;
    }

    private static boolean getBool(JsonNode node, String field, boolean def) {
        JsonNode n = node.get(field);
        return n != null && !n.isNull() ? n.asBoolean() : def;
    }

    private static int getInt(JsonNode node, String field, int def) {
        JsonNode n = node.get(field);
        return n != null && !n.isNull() ? n.asInt() : def;
    }

    private static long getLong(JsonNode node, String field, long def) {
        JsonNode n = node.get(field);
        return n != null && !n.isNull() ? n.asLong() : def;
    }

    private static List<String> getStringList(JsonNode node, String field, List<String> def) {
        JsonNode n = node.get(field);
        if (n != null && n.isArray()) {
            List<String> result = new ArrayList<>();
            for (JsonNode e : n) {
                result.add(e.asText());
            }
            return result;
        }
        return def;
    }

    public AppSection getApp() { return app; }
    public AuthSection getAuth() { return auth; }
    public DatabaseSection getDatabase() { return database; }
    public ServerSection getServer() { return server; }
    public VideoSection getVideo() { return video; }
    public LoggingSection getLogging() { return logging; }
    public TelegramSection getTelegram() { return telegram; }
    public UploadsSection getUploads() { return uploads; }
    public FeaturesSection getFeatures() { return features; }
    public MailSection getMail() { return mail; }
    public GoogleSection getGoogle() { return google; }

    public static class AppSection {
        private String name = "Kiselgram";
        private String version = "1.0.0";
        private boolean debug = false;
        private String host = "0.0.0.0";
        private int port = 8080;
        private String secretKey = "change-me-in-production";

        public String getName() { return name; }
        public String getVersion() { return version; }
        public boolean isDebug() { return debug; }
        public String getHost() { return host; }
        public int getPort() { return port; }
        public String getSecretKey() { return secretKey; }
    }

    public static class AuthSection {
        private int port = 8081;

        public int getPort() { return port; }
    }

    public static class DatabaseSection {
        private String url = "jdbc:h2:mem:kiselgramdb";
        private boolean echo = false;

        public String getUrl() { return url; }
        public boolean isEcho() { return echo; }
    }

    public static class ServerSection {
        private int workers = 4;
        private boolean threaded = true;

        public int getWorkers() { return workers; }
        public boolean isThreaded() { return threaded; }
    }

    public static class VideoSection {
        private boolean enabled = false;
        private String host = "127.0.0.1";
        private int port = 5000;
        private int quality = 30;
        private long maxSize = 50 * 1024 * 1024;

        public boolean isEnabled() { return enabled; }
        public String getHost() { return host; }
        public int getPort() { return port; }
        public int getQuality() { return quality; }
        public long getMaxSize() { return maxSize; }
    }

    public static class LoggingSection {
        private String level = "INFO";
        private String format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s";
        private String file = "logs/kiselgram.log";
        private long maxSize = 10 * 1024 * 1024;
        private int backupCount = 5;

        public String getLevel() { return level; }
        public String getFormat() { return format; }
        public String getFile() { return file; }
        public long getMaxSize() { return maxSize; }
        public int getBackupCount() { return backupCount; }
    }

    public static class TelegramSection {
        private String botToken = "";
        private String webhookUrl = "";

        public String getBotToken() { return botToken; }
        public String getWebhookUrl() { return webhookUrl; }
    }

    public static class UploadsSection {
        private String folder = "uploads";
        private long maxSize = 100 * 1024 * 1024;
        private List<String> allowedImages = List.of("jpg", "jpeg", "png", "gif", "bmp", "webp");
        private List<String> allowedDocuments = List.of("pdf", "doc", "docx", "txt", "rtf");
        private List<String> allowedVideos = List.of("mp4", "avi", "mov", "mkv", "webm");

        public String getFolder() { return folder; }
        public long getMaxSize() { return maxSize; }
        public List<String> getAllowedImages() { return allowedImages; }
        public List<String> getAllowedDocuments() { return allowedDocuments; }
        public List<String> getAllowedVideos() { return allowedVideos; }
    }

    public static class FeaturesSection {
        private boolean groups = true;
        private boolean channels = true;
        private boolean bots = true;
        private boolean videoStreaming = false;
        private boolean fileSharing = true;
        private boolean reactions = true;
        private boolean twoFactorAuth = true;
        private boolean premium = true;

        public boolean isGroups() { return groups; }
        public boolean isChannels() { return channels; }
        public boolean isBots() { return bots; }
        public boolean isVideoStreaming() { return videoStreaming; }
        public boolean isFileSharing() { return fileSharing; }
        public boolean isReactions() { return reactions; }
        public boolean isTwoFactorAuth() { return twoFactorAuth; }
        public boolean isPremium() { return premium; }
    }

    public static class MailSection {
        private String server = "smtp.gmail.com";
        private int port = 587;
        private String username = "";
        private String password = "";
        private String senderName = "Kiselgram";
        private String senderEmail = "noreply@kiselgram.com";

        public String getServer() { return server; }
        public int getPort() { return port; }
        public String getUsername() { return username; }
        public String getPassword() { return password; }
        public String getSenderName() { return senderName; }
        public String getSenderEmail() { return senderEmail; }
    }

    public static class GoogleSection {
        private String clientId = "";
        private String clientSecret = "";
        private String redirectUri = "http://127.0.0.1:8080/api/auth/oauth/google/callback";

        public String getClientId() { return clientId; }
        public String getClientSecret() { return clientSecret; }
        public String getRedirectUri() { return redirectUri; }
    }
}
