package ru.kiselgram.web.util;

import ru.kiselgram.web.config.AppConfig;
import nl.martijndwars.webpush.Notification;
import nl.martijndwars.webpush.PushService;
import nl.martijndwars.webpush.Subscription;

import java.security.GeneralSecurityException;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public final class PushUtil {

    private static volatile PushUtil instance;
    private final PushService pushService;
    private final Map<String, Long> rateLimitMap = new ConcurrentHashMap<>();
    private static final long RATE_LIMIT_WINDOW_MS = 1000;

    private PushUtil() {
        AppConfig config = AppConfig.getInstance();
        pushService = new PushService();

        String vapidPublicKey = System.getenv("VAPID_PUBLIC_KEY");
        String vapidPrivateKey = System.getenv("VAPID_PRIVATE_KEY");

        if (vapidPublicKey != null && vapidPrivateKey != null && !vapidPublicKey.isBlank() && !vapidPrivateKey.isBlank()) {
            try {
                pushService.setPublicKey(vapidPublicKey);
                pushService.setPrivateKey(vapidPrivateKey);
            } catch (GeneralSecurityException e) {
                System.err.println("Failed to set VAPID keys: " + e.getMessage());
            }
        }

        pushService.setSubject("mailto:admin@" + config.getApp().getName().toLowerCase() + ".com");
    }

    public static PushUtil getInstance() {
        if (instance == null) {
            synchronized (PushUtil.class) {
                if (instance == null) {
                    instance = new PushUtil();
                }
            }
        }
        return instance;
    }

    public static String generateVapidKeys() {
        return "VAPID key generation not supported at runtime."
             + " Use a command-line tool or visit https://www.vapidkeys.com";
    }

    public void sendPushNotification(PushSubscription subscription, String title, String body) {
        sendPushNotification(subscription, title, body, null, null, null, null);
    }

    public void sendPushNotification(PushSubscription subscription, String title, String body,
                                      String icon, String badge, String image, String clickUrl) {
        if (subscription == null) return;

        String rateKey = subscription.endpoint;
        long now = System.currentTimeMillis();
        Long lastSend = rateLimitMap.get(rateKey);
        if (lastSend != null && (now - lastSend) < RATE_LIMIT_WINDOW_MS) {
            return;
        }
        rateLimitMap.put(rateKey, now);

        try {
            Subscription.Keys keys = new Subscription.Keys();
            keys.p256dh = subscription.p256dh;
            keys.auth = subscription.auth;

            Subscription sub = new Subscription();
            sub.endpoint = subscription.endpoint;
            sub.keys = keys;

            StringBuilder payload = new StringBuilder();
            payload.append("{\n");
            payload.append("  \"title\": \"").append(escapeJson(title != null ? title : "")).append("\",\n");
            payload.append("  \"body\": \"").append(escapeJson(body != null ? body : "")).append("\",\n");
            if (icon != null) {
                payload.append("  \"icon\": \"").append(escapeJson(icon)).append("\",\n");
            }
            if (badge != null) {
                payload.append("  \"badge\": \"").append(escapeJson(badge)).append("\",\n");
            }
            if (image != null) {
                payload.append("  \"image\": \"").append(escapeJson(image)).append("\",\n");
            }
            if (clickUrl != null) {
                payload.append("  \"data\": {\"url\": \"").append(escapeJson(clickUrl)).append("\"},\n");
            }
            payload.append("  \"vibrate\": [200, 100, 200]\n");
            payload.append("}");

            Notification notification = new Notification(sub, payload.toString());
            pushService.send(notification);
        } catch (Exception e) {
            System.err.println("Push notification failed: " + e.getMessage());
        }
    }

    private static String escapeJson(String input) {
        if (input == null) return "";
        return input
                .replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t");
    }

    public static class PushSubscription {
        private final String endpoint;
        private final String p256dh;
        private final String auth;

        public PushSubscription(String endpoint, String p256dh, String auth) {
            this.endpoint = endpoint;
            this.p256dh = p256dh;
            this.auth = auth;
        }

        public String getEndpoint() { return endpoint; }
        public String getP256dh() { return p256dh; }
        public String getAuth() { return auth; }
    }
}
