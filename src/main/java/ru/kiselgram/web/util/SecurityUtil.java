package ru.kiselgram.web.util;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.Base64;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.regex.Pattern;

public final class SecurityUtil {

    private static final SecureRandom RNG = new SecureRandom();

    private static final ConcurrentHashMap<String, RateLimitEntry> RATE_LIMITER = new ConcurrentHashMap<>();
    private static final long RATE_LIMIT_CLEANUP_INTERVAL_MS = 60_000;
    private static volatile long lastCleanup = System.currentTimeMillis();

    private static final Pattern SCRIPT_TAG = Pattern.compile(
            "<\\s*script\\b[^>]*>(.*?)<\\s*/\\s*script\\s*>",
            Pattern.CASE_INSENSITIVE | Pattern.DOTALL
    );
    private static final Pattern EVENT_HANDLER = Pattern.compile(
            "\\s+on\\w+\\s*=\\s*\"[^\"]*\"|\\s+on\\w+\\s*=\\s*'[^']*'|\\s+on\\w+\\s*=\\s*[^\\s>]+",
            Pattern.CASE_INSENSITIVE
    );
    private static final Pattern JAVASCRIPT_PREFIX = Pattern.compile(
            "^\\s*javascript\\s*:",
            Pattern.CASE_INSENSITIVE
    );

    public static final String CSP_POLICY = String.join("; ",
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net",
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://fonts.googleapis.com https://p.typekit.net",
            "img-src 'self' data: blob: https:",
            "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com",
            "connect-src 'self' ws: wss: https://cdn.jsdelivr.net",
            "media-src 'self'",
            "frame-ancestors 'none'",
            "form-action 'self'",
            "base-uri 'self'"
    );

    public static final Map<String, String> SECURITY_HEADERS = Map.of(
            "X-Content-Type-Options", "nosniff",
            "X-XSS-Protection", "1; mode=block",
            "X-Frame-Options", "DENY",
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains",
            "Referrer-Policy", "strict-origin-when-cross-origin",
            "Permissions-Policy", "camera=(), microphone=(), geolocation=()",
            "Content-Security-Policy", CSP_POLICY
    );

    private SecurityUtil() {}

    public static Map<String, String> addSecurityHeaders() {
        return SECURITY_HEADERS;
    }

    public static boolean rateLimit(String key, int maxRequests, long windowSeconds) {
        long now = System.currentTimeMillis();
        if (now - lastCleanup > RATE_LIMIT_CLEANUP_INTERVAL_MS) {
            cleanup();
        }
        RateLimitEntry entry = RATE_LIMITER.compute(key, (k, v) -> {
            if (v == null || now - v.windowStart > windowSeconds * 1000) {
                return new RateLimitEntry(now, 1);
            }
            v.count++;
            return v;
        });
        return entry.count <= maxRequests;
    }

    private static void cleanup() {
        long now = System.currentTimeMillis();
        long cutoff = now - 300_000;
        RATE_LIMITER.entrySet().removeIf(e -> e.getValue().windowStart < cutoff);
        lastCleanup = System.currentTimeMillis();
    }

    public static String generateCsrfToken() {
        byte[] token = new byte[32];
        RNG.nextBytes(token);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(token);
    }

    public static boolean validateCsrfToken(String token, String storedToken) {
        if (token == null || storedToken == null) return false;
        return MessageDigest.isEqual(
                token.getBytes(StandardCharsets.UTF_8),
                storedToken.getBytes(StandardCharsets.UTF_8)
        );
    }

    public static String validatePassword(String password) {
        if (password == null) return "Password is required";
        if (password.length() < 8) return "Password must be at least 8 characters";
        if (password.length() > 128) return "Password must be at most 128 characters";
        if (!password.matches(".*[a-zA-Z].*")) return "Password must contain at least one letter";
        if (!password.matches(".*[0-9].*")) return "Password must contain at least one digit";
        return null;
    }

    public static String sanitizeString(String input, int maxLength) {
        if (input == null) return null;
        String result = input.trim();
        if (maxLength > 0 && result.length() > maxLength) {
            result = result.substring(0, maxLength);
        }
        StringBuilder sb = new StringBuilder(result.length());
        for (int i = 0; i < result.length(); i++) {
            char c = result.charAt(i);
            if (c >= 32 || c == '\n' || c == '\r' || c == '\t') {
                sb.append(c);
            }
        }
        return sb.toString();
    }

    public static String sanitizeHtml(String input) {
        if (input == null) return null;
        String result = SCRIPT_TAG.matcher(input).replaceAll("");
        result = EVENT_HANDLER.matcher(result).replaceAll(" ");
        result = JAVASCRIPT_PREFIX.matcher(result).replaceAll("");
        return result;
    }

    private static class RateLimitEntry {
        final long windowStart;
        int count;

        RateLimitEntry(long windowStart, int count) {
            this.windowStart = windowStart;
            this.count = count;
        }
    }
}
