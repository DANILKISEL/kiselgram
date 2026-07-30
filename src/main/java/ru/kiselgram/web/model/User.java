package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.LocalDateTime;
import java.util.Base64;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

@Entity
@Table(name = "users")
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true, length = 80)
    private String username;

    @Column(unique = true, length = 120)
    private String email;

    @Column(name = "email_verified")
    private boolean emailVerified;

    @Column(name = "display_name", length = 100)
    private String displayName;

    @Column(name = "password_hash", nullable = false, length = 120)
    private String passwordHash;

    @Column(name = "telegram_chat_id", length = 50)
    private String telegramChatId;

    @Column(name = "telegram_username", length = 80)
    private String telegramUsername;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(columnDefinition = "TEXT")
    private String bio;

    @Column(name = "avatar_url", length = 500)
    private String avatarUrl;

    @Column(name = "last_seen")
    private LocalDateTime lastSeen;

    @Column(name = "is_online")
    private boolean isOnline;

    @Column(name = "is_admin")
    private boolean isAdmin;

    @Column(name = "notification_sound", length = 100)
    private String notificationSound;

    @Column(name = "mute_all")
    private boolean muteAll;

    @Column(name = "do_not_disturb")
    private boolean doNotDisturb;

    @Column(name = "is_bot")
    private boolean isBot;

    @Column(name = "bot_owner_id")
    private Long botOwnerId;

    @Column(name = "bot_token", length = 255)
    private String botToken;

    @Column(name = "bot_webapp_url", length = 500)
    private String botWebappUrl;

    @Column(name = "status_emoji", length = 20)
    private String statusEmoji;

    @Column(name = "privacy_last_seen", length = 20)
    private String privacyLastSeen;

    @Column(name = "privacy_photo", length = 20)
    private String privacyPhoto;

    @Column(name = "privacy_forward", length = 20)
    private String privacyForward;

    @Column(name = "privacy_calls", length = 20)
    private String privacyCalls;

    @Column(name = "privacy_messages", length = 20)
    private String privacyMessages;

    @Column(length = 20)
    private String theme;

    @Column(name = "font_size")
    private int fontSize;

    @Column(name = "bubble_radius")
    private int bubbleRadius;

    @Column(name = "font_family", length = 50)
    private String fontFamily;

    @Column(name = "my_message_color", length = 20)
    private String myMessageColor;

    @Column(name = "their_message_color", length = 20)
    private String theirMessageColor;

    @Column(length = 50)
    private String wallpaper;

    @Column(name = "wallpaper_image", length = 500)
    private String wallpaperImage;

    @Column(name = "is_deleted")
    private boolean isDeleted;

    @Column(name = "deleted_at")
    private LocalDateTime deletedAt;

    @Column(name = "google_id", length = 100)
    private String googleId;

    @Column(name = "profile_pic", length = 500)
    private String profilePic;

    @OneToMany(mappedBy = "sender")
    private Set<Message> sentMessages = new HashSet<>();

    @OneToMany(mappedBy = "receiver")
    private Set<Message> receivedMessages = new HashSet<>();

    @OneToMany(mappedBy = "user")
    private Set<Story> stories = new HashSet<>();

    @OneToMany(mappedBy = "user")
    private Set<Contact> contacts = new HashSet<>();

    @OneToMany(mappedBy = "contactUser")
    private Set<Contact> contactOf = new HashSet<>();

    @OneToMany(mappedBy = "user")
    private Set<PushSubscription> pushSubscriptions = new HashSet<>();

    @OneToMany(mappedBy = "user")
    private Set<UserSession> sessions = new HashSet<>();

    @OneToMany(mappedBy = "user")
    private Set<Favorite> favorites = new HashSet<>();

    @OneToMany(mappedBy = "user")
    private Set<RecentSearch> recentSearches = new HashSet<>();

    @OneToMany(mappedBy = "user")
    private Set<PinnedChat> pinnedChats = new HashSet<>();

    @OneToMany(mappedBy = "user")
    private Set<BlockedUser> blockedUsers = new HashSet<>();

    @OneToMany(mappedBy = "blockedUser")
    private Set<BlockedUser> blockedBy = new HashSet<>();

    @OneToMany(mappedBy = "user")
    private Set<Report> reports = new HashSet<>();

    public User() {
        this.createdAt = LocalDateTime.now();
    }

    public User(Long id, String username, String email, boolean emailVerified, String displayName,
                String passwordHash, String telegramChatId, String telegramUsername,
                LocalDateTime createdAt, String bio, String avatarUrl, LocalDateTime lastSeen,
                boolean isOnline, boolean isAdmin, String notificationSound, boolean muteAll,
                boolean doNotDisturb, boolean isBot, Long botOwnerId, String botToken,
                String botWebappUrl, String statusEmoji, String privacyLastSeen,
                String privacyPhoto, String privacyForward, String privacyCalls,
                String privacyMessages, String theme, int fontSize, int bubbleRadius,
                String fontFamily, String myMessageColor, String theirMessageColor,
                String wallpaper, String wallpaperImage, boolean isDeleted,
                LocalDateTime deletedAt, String googleId, String profilePic) {
        this.id = id;
        this.username = username;
        this.email = email;
        this.emailVerified = emailVerified;
        this.displayName = displayName;
        this.passwordHash = passwordHash;
        this.telegramChatId = telegramChatId;
        this.telegramUsername = telegramUsername;
        this.createdAt = createdAt;
        this.bio = bio;
        this.avatarUrl = avatarUrl;
        this.lastSeen = lastSeen;
        this.isOnline = isOnline;
        this.isAdmin = isAdmin;
        this.notificationSound = notificationSound;
        this.muteAll = muteAll;
        this.doNotDisturb = doNotDisturb;
        this.isBot = isBot;
        this.botOwnerId = botOwnerId;
        this.botToken = botToken;
        this.botWebappUrl = botWebappUrl;
        this.statusEmoji = statusEmoji;
        this.privacyLastSeen = privacyLastSeen;
        this.privacyPhoto = privacyPhoto;
        this.privacyForward = privacyForward;
        this.privacyCalls = privacyCalls;
        this.privacyMessages = privacyMessages;
        this.theme = theme;
        this.fontSize = fontSize;
        this.bubbleRadius = bubbleRadius;
        this.fontFamily = fontFamily;
        this.myMessageColor = myMessageColor;
        this.theirMessageColor = theirMessageColor;
        this.wallpaper = wallpaper;
        this.wallpaperImage = wallpaperImage;
        this.isDeleted = isDeleted;
        this.deletedAt = deletedAt;
        this.googleId = googleId;
        this.profilePic = profilePic;
    }

    public void setPassword(String rawPassword) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(rawPassword.getBytes(StandardCharsets.UTF_8));
            this.passwordHash = Base64.getEncoder().encodeToString(hash);
        } catch (Exception e) {
            throw new RuntimeException("Failed to hash password", e);
        }
    }

    public boolean checkPassword(String rawPassword) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(rawPassword.getBytes(StandardCharsets.UTF_8));
            return this.passwordHash.equals(Base64.getEncoder().encodeToString(hash));
        } catch (Exception e) {
            return false;
        }
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("id", id);
        map.put("username", username);
        map.put("email", email);
        map.put("email_verified", emailVerified);
        map.put("display_name", displayName);
        map.put("telegram_chat_id", telegramChatId);
        map.put("telegram_username", telegramUsername);
        map.put("created_at", createdAt);
        map.put("bio", bio);
        map.put("avatar_url", avatarUrl);
        map.put("last_seen", lastSeen);
        map.put("is_online", isOnline);
        map.put("is_admin", isAdmin);
        map.put("notification_sound", notificationSound);
        map.put("mute_all", muteAll);
        map.put("do_not_disturb", doNotDisturb);
        map.put("is_bot", isBot);
        map.put("bot_owner_id", botOwnerId);
        map.put("status_emoji", statusEmoji);
        map.put("privacy_last_seen", privacyLastSeen);
        map.put("privacy_photo", privacyPhoto);
        map.put("privacy_forward", privacyForward);
        map.put("privacy_calls", privacyCalls);
        map.put("privacy_messages", privacyMessages);
        map.put("theme", theme);
        map.put("font_size", fontSize);
        map.put("bubble_radius", bubbleRadius);
        map.put("font_family", fontFamily);
        map.put("my_message_color", myMessageColor);
        map.put("their_message_color", theirMessageColor);
        map.put("wallpaper", wallpaper);
        map.put("wallpaper_image", wallpaperImage);
        map.put("is_deleted", isDeleted);
        map.put("deleted_at", deletedAt);
        map.put("google_id", googleId);
        map.put("profile_pic", profilePic);
        return map;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getUsername() { return username; }
    public void setUsername(String username) { this.username = username; }
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    public boolean isEmailVerified() { return emailVerified; }
    public void setEmailVerified(boolean emailVerified) { this.emailVerified = emailVerified; }
    public String getDisplayName() { return displayName; }
    public void setDisplayName(String displayName) { this.displayName = displayName; }
    public String getPasswordHash() { return passwordHash; }
    public void setPasswordHash(String passwordHash) { this.passwordHash = passwordHash; }
    public String getTelegramChatId() { return telegramChatId; }
    public void setTelegramChatId(String telegramChatId) { this.telegramChatId = telegramChatId; }
    public String getTelegramUsername() { return telegramUsername; }
    public void setTelegramUsername(String telegramUsername) { this.telegramUsername = telegramUsername; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    public String getBio() { return bio; }
    public void setBio(String bio) { this.bio = bio; }
    public String getAvatarUrl() { return avatarUrl; }
    public void setAvatarUrl(String avatarUrl) { this.avatarUrl = avatarUrl; }
    public LocalDateTime getLastSeen() { return lastSeen; }
    public void setLastSeen(LocalDateTime lastSeen) { this.lastSeen = lastSeen; }
    public boolean isOnline() { return isOnline; }
    public void setOnline(boolean online) { isOnline = online; }
    public boolean isAdmin() { return isAdmin; }
    public void setAdmin(boolean admin) { isAdmin = admin; }
    public String getNotificationSound() { return notificationSound; }
    public void setNotificationSound(String notificationSound) { this.notificationSound = notificationSound; }
    public boolean isMuteAll() { return muteAll; }
    public void setMuteAll(boolean muteAll) { this.muteAll = muteAll; }
    public boolean isDoNotDisturb() { return doNotDisturb; }
    public void setDoNotDisturb(boolean doNotDisturb) { this.doNotDisturb = doNotDisturb; }
    public boolean isBot() { return isBot; }
    public void setBot(boolean bot) { isBot = bot; }
    public Long getBotOwnerId() { return botOwnerId; }
    public void setBotOwnerId(Long botOwnerId) { this.botOwnerId = botOwnerId; }
    public String getBotToken() { return botToken; }
    public void setBotToken(String botToken) { this.botToken = botToken; }
    public String getBotWebappUrl() { return botWebappUrl; }
    public void setBotWebappUrl(String botWebappUrl) { this.botWebappUrl = botWebappUrl; }
    public String getStatusEmoji() { return statusEmoji; }
    public void setStatusEmoji(String statusEmoji) { this.statusEmoji = statusEmoji; }
    public String getPrivacyLastSeen() { return privacyLastSeen; }
    public void setPrivacyLastSeen(String privacyLastSeen) { this.privacyLastSeen = privacyLastSeen; }
    public String getPrivacyPhoto() { return privacyPhoto; }
    public void setPrivacyPhoto(String privacyPhoto) { this.privacyPhoto = privacyPhoto; }
    public String getPrivacyForward() { return privacyForward; }
    public void setPrivacyForward(String privacyForward) { this.privacyForward = privacyForward; }
    public String getPrivacyCalls() { return privacyCalls; }
    public void setPrivacyCalls(String privacyCalls) { this.privacyCalls = privacyCalls; }
    public String getPrivacyMessages() { return privacyMessages; }
    public void setPrivacyMessages(String privacyMessages) { this.privacyMessages = privacyMessages; }
    public String getTheme() { return theme; }
    public void setTheme(String theme) { this.theme = theme; }
    public int getFontSize() { return fontSize; }
    public void setFontSize(int fontSize) { this.fontSize = fontSize; }
    public int getBubbleRadius() { return bubbleRadius; }
    public void setBubbleRadius(int bubbleRadius) { this.bubbleRadius = bubbleRadius; }
    public String getFontFamily() { return fontFamily; }
    public void setFontFamily(String fontFamily) { this.fontFamily = fontFamily; }
    public String getMyMessageColor() { return myMessageColor; }
    public void setMyMessageColor(String myMessageColor) { this.myMessageColor = myMessageColor; }
    public String getTheirMessageColor() { return theirMessageColor; }
    public void setTheirMessageColor(String theirMessageColor) { this.theirMessageColor = theirMessageColor; }
    public String getWallpaper() { return wallpaper; }
    public void setWallpaper(String wallpaper) { this.wallpaper = wallpaper; }
    public String getWallpaperImage() { return wallpaperImage; }
    public void setWallpaperImage(String wallpaperImage) { this.wallpaperImage = wallpaperImage; }
    public boolean isDeleted() { return isDeleted; }
    public void setDeleted(boolean deleted) { isDeleted = deleted; }
    public LocalDateTime getDeletedAt() { return deletedAt; }
    public void setDeletedAt(LocalDateTime deletedAt) { this.deletedAt = deletedAt; }
    public String getGoogleId() { return googleId; }
    public void setGoogleId(String googleId) { this.googleId = googleId; }
    public String getProfilePic() { return profilePic; }
    public void setProfilePic(String profilePic) { this.profilePic = profilePic; }
    public Set<Message> getSentMessages() { return sentMessages; }
    public void setSentMessages(Set<Message> sentMessages) { this.sentMessages = sentMessages; }
    public Set<Message> getReceivedMessages() { return receivedMessages; }
    public void setReceivedMessages(Set<Message> receivedMessages) { this.receivedMessages = receivedMessages; }
    public Set<Story> getStories() { return stories; }
    public void setStories(Set<Story> stories) { this.stories = stories; }
    public Set<Contact> getContacts() { return contacts; }
    public void setContacts(Set<Contact> contacts) { this.contacts = contacts; }
    public Set<Contact> getContactOf() { return contactOf; }
    public void setContactOf(Set<Contact> contactOf) { this.contactOf = contactOf; }
    public Set<PushSubscription> getPushSubscriptions() { return pushSubscriptions; }
    public void setPushSubscriptions(Set<PushSubscription> pushSubscriptions) { this.pushSubscriptions = pushSubscriptions; }
    public Set<UserSession> getSessions() { return sessions; }
    public void setSessions(Set<UserSession> sessions) { this.sessions = sessions; }
    public Set<Favorite> getFavorites() { return favorites; }
    public void setFavorites(Set<Favorite> favorites) { this.favorites = favorites; }
    public Set<RecentSearch> getRecentSearches() { return recentSearches; }
    public void setRecentSearches(Set<RecentSearch> recentSearches) { this.recentSearches = recentSearches; }
    public Set<PinnedChat> getPinnedChats() { return pinnedChats; }
    public void setPinnedChats(Set<PinnedChat> pinnedChats) { this.pinnedChats = pinnedChats; }
    public Set<BlockedUser> getBlockedUsers() { return blockedUsers; }
    public void setBlockedUsers(Set<BlockedUser> blockedUsers) { this.blockedUsers = blockedUsers; }
    public Set<BlockedUser> getBlockedBy() { return blockedBy; }
    public void setBlockedBy(Set<BlockedUser> blockedBy) { this.blockedBy = blockedBy; }
    public Set<Report> getReports() { return reports; }
    public void setReports(Set<Report> reports) { this.reports = reports; }
}
