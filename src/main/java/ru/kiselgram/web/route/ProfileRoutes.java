package ru.kiselgram.web.route;

import ru.kiselgram.web.model.User;
import ru.kiselgram.web.repository.UserRepository;
import ru.kiselgram.web.service.AuthService;
import ru.kiselgram.web.service.DatabaseService;
import ru.kiselgram.web.service.MessageService;
import ru.kiselgram.web.service.ChatService;
import ru.kiselgram.web.service.StoryService;
import ru.kiselgram.web.service.AdminService;
import org.hibernate.Session;
import io.javalin.Javalin;

import java.util.*;

import static ru.kiselgram.web.route.RouteHelper.*;

public class ProfileRoutes {

    private static AuthService authService;

    public static void registerRoutes(Javalin app, AuthService as, MessageService messageService,
                                      ChatService chatService, StoryService storyService,
                                      AdminService adminService) {
        authService = as;

        app.get("/api/profile", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> data = new HashMap<>();
            data.put("user_id", user.getId());
            data.put("username", user.getUsername());
            data.put("display_name", user.getDisplayName());
            data.put("email", user.getEmail());
            data.put("email_verified", user.isEmailVerified());
            data.put("avatar_url", user.getAvatarUrl());
            data.put("bio", user.getBio());
            data.put("status_emoji", user.getStatusEmoji());
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                var prem = listMaps(s, "SELECT is_premium FROM user_premium WHERE user_id = :uid", "uid", user.getId());
                data.put("is_premium", !prem.isEmpty() && Boolean.TRUE.equals(prem.get(0).get("is_premium")));
            }
            data.put("is_admin", user.isAdmin());
            ctx.json(ok(data));
        });

        app.put("/api/profile", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                User managed = s.get(User.class, user.getId());
                if (body.containsKey("display_name")) managed.setDisplayName((String) body.get("display_name"));
                if (body.containsKey("bio")) managed.setBio((String) body.get("bio"));
                if (body.containsKey("avatar_url")) managed.setAvatarUrl((String) body.get("avatar_url"));
                if (body.containsKey("status_emoji")) managed.setStatusEmoji((String) body.get("status_emoji"));
                if (body.containsKey("username")) managed.setUsername((String) body.get("username"));
                s.merge(managed);
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Profile updated")));
        });

        app.get("/api/user/{userId}", ctx -> {
            User currentUser = authService.getCurrentUser(ctx);
            if (currentUser == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            long userId = ctx.pathParamAsClass("userId", Long.class).get();
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                var rows = listMaps(s, "SELECT id, username, display_name, avatar_url, bio, status_emoji, is_online FROM users WHERE id = :id AND is_deleted = false", "id", userId);
                if (rows.isEmpty()) { ctx.status(404).json(err("NOT_FOUND", "User not found")); return; }
                ctx.json(ok(rows.get(0)));
            }
        });

        app.put("/api/profile/settings", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                User managed = s.get(User.class, user.getId());
                if (body.containsKey("theme")) managed.setTheme((String) body.get("theme"));
                if (body.containsKey("font_size")) managed.setFontSize(body.get("font_size") instanceof Number ? ((Number) body.get("font_size")).intValue() : Integer.parseInt((String) body.get("font_size")));
                if (body.containsKey("bubble_radius")) managed.setBubbleRadius(((Number) body.get("bubble_radius")).intValue());
                if (body.containsKey("font_family")) managed.setFontFamily((String) body.get("font_family"));
                if (body.containsKey("my_message_color")) managed.setMyMessageColor((String) body.get("my_message_color"));
                if (body.containsKey("their_message_color")) managed.setTheirMessageColor((String) body.get("their_message_color"));
                if (body.containsKey("wallpaper")) managed.setWallpaper((String) body.get("wallpaper"));
                s.merge(managed);
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Settings saved")));
        });

        app.get("/api/profile/privacy", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> data = new HashMap<>();
            data.put("last_seen", user.getPrivacyLastSeen() != null ? user.getPrivacyLastSeen() : "everyone");
            data.put("profile_photo", user.getPrivacyPhoto() != null ? user.getPrivacyPhoto() : "everyone");
            data.put("forward", user.getPrivacyForward() != null ? user.getPrivacyForward() : "everyone");
            data.put("calls", user.getPrivacyCalls() != null ? user.getPrivacyCalls() : "everyone");
            ctx.json(ok(data));
        });

        app.put("/api/profile/privacy", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                User managed = s.get(User.class, user.getId());
                if (body.containsKey("privacy_last_seen")) managed.setPrivacyLastSeen((String) body.get("privacy_last_seen"));
                if (body.containsKey("privacy_photo")) managed.setPrivacyPhoto((String) body.get("privacy_photo"));
                if (body.containsKey("privacy_forward")) managed.setPrivacyForward((String) body.get("privacy_forward"));
                if (body.containsKey("privacy_calls")) managed.setPrivacyCalls((String) body.get("privacy_calls"));
                s.merge(managed);
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Privacy saved")));
        });

        app.put("/api/profile/notifications", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                User managed = s.get(User.class, user.getId());
                if (body.containsKey("notification_sound")) managed.setNotificationSound((String) body.get("notification_sound"));
                if (body.containsKey("mute_all")) managed.setMuteAll(Boolean.TRUE.equals(body.get("mute_all")));
                if (body.containsKey("do_not_disturb")) managed.setDoNotDisturb(Boolean.TRUE.equals(body.get("do_not_disturb")));
                s.merge(managed);
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Notifications saved")));
        });

        app.get("/api/users", ctx -> {
            String search = ctx.queryParam("search");
            UserRepository repo = new UserRepository();
            List<User> users;
            if (search != null && !search.isBlank()) {
                users = repo.search(search, 1, 50);
            } else {
                users = repo.findAll(1, 50);
            }
            ctx.json(ok(users.stream().map(u -> {
                Map<String, Object> m = new HashMap<>();
                m.put("id", u.getId());
                m.put("username", u.getUsername());
                m.put("display_name", u.getDisplayName());
                m.put("avatar_url", u.getAvatarUrl());
                m.put("bio", u.getBio());
                return m;
            }).toList()));
        });
    }
}
