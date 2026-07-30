package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.util.HashMap;
import java.util.Map;

@Entity
@Table(name = "user_ksettings")
public class UserKSettings {

    @Id
    private Long userId;

    @OneToOne
    @MapsId
    @JoinColumn(name = "user_id")
    private User user;

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

    @Column(name = "notification_sound", length = 100)
    private String notificationSound;

    @Column(name = "mute_all")
    private boolean muteAll;

    @Column(name = "do_not_disturb")
    private boolean doNotDisturb;

    @Column(name = "language", length = 10)
    private String language;

    public UserKSettings() {}

    public UserKSettings(Long userId, User user, String theme, int fontSize, int bubbleRadius,
                         String fontFamily, String myMessageColor, String theirMessageColor,
                         String wallpaper, String wallpaperImage, String notificationSound,
                         boolean muteAll, boolean doNotDisturb, String language) {
        this.userId = userId;
        this.user = user;
        this.theme = theme;
        this.fontSize = fontSize;
        this.bubbleRadius = bubbleRadius;
        this.fontFamily = fontFamily;
        this.myMessageColor = myMessageColor;
        this.theirMessageColor = theirMessageColor;
        this.wallpaper = wallpaper;
        this.wallpaperImage = wallpaperImage;
        this.notificationSound = notificationSound;
        this.muteAll = muteAll;
        this.doNotDisturb = doNotDisturb;
        this.language = language;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("user_id", userId);
        map.put("theme", theme);
        map.put("font_size", fontSize);
        map.put("bubble_radius", bubbleRadius);
        map.put("font_family", fontFamily);
        map.put("my_message_color", myMessageColor);
        map.put("their_message_color", theirMessageColor);
        map.put("wallpaper", wallpaper);
        map.put("wallpaper_image", wallpaperImage);
        map.put("notification_sound", notificationSound);
        map.put("mute_all", muteAll);
        map.put("do_not_disturb", doNotDisturb);
        map.put("language", language);
        return map;
    }

    public Long getUserId() { return userId; }
    public void setUserId(Long userId) { this.userId = userId; }
    public User getUser() { return user; }
    public void setUser(User user) { this.user = user; }
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
    public String getNotificationSound() { return notificationSound; }
    public void setNotificationSound(String notificationSound) { this.notificationSound = notificationSound; }
    public boolean isMuteAll() { return muteAll; }
    public void setMuteAll(boolean muteAll) { this.muteAll = muteAll; }
    public boolean isDoNotDisturb() { return doNotDisturb; }
    public void setDoNotDisturb(boolean doNotDisturb) { this.doNotDisturb = doNotDisturb; }
    public String getLanguage() { return language; }
    public void setLanguage(String language) { this.language = language; }
}
