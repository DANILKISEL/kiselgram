package ru.kiselgram.web.route;

import ru.kiselgram.web.model.User;
import ru.kiselgram.web.service.AuthService;
import ru.kiselgram.web.service.MessageService;
import ru.kiselgram.web.service.ChatService;
import ru.kiselgram.web.service.StoryService;
import ru.kiselgram.web.service.AdminService;
import ru.kiselgram.web.service.DatabaseService;
import org.hibernate.Session;
import io.javalin.Javalin;

import java.util.Map;

public class KSettingsRoutes {

    public static void registerRoutes(Javalin app, AuthService authService, MessageService messageService,
                                      ChatService chatService, StoryService storyService,
                                      AdminService adminService) {

        app.get("/api/k_settings", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(error("UNAUTHORIZED", "Not authenticated")); return; }
            ctx.json(success(Map.of(
                    "theme", user.getTheme() != null ? user.getTheme() : "dark",
                    "font_size", String.valueOf(user.getFontSize() == 0 ? 16 : user.getFontSize()),
                    "font_family", user.getFontFamily() != null ? user.getFontFamily() : "system-ui"
            )));
        });

        app.put("/api/k_settings", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(error("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                User managed = s.get(User.class, user.getId());
                if (body.containsKey("theme")) managed.setTheme((String) body.get("theme"));
                if (body.containsKey("font_size")) managed.setFontSize(Integer.parseInt((String) body.get("font_size")));
                if (body.containsKey("font_family")) managed.setFontFamily((String) body.get("font_family"));
                s.merge(managed);
                s.getTransaction().commit();
            }
            ctx.json(success(Map.of("message", "Settings saved")));
        });

        app.get("/api/k/settings", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(error("UNAUTHORIZED", "Not authenticated")); return; }
            ctx.json(success(Map.of(
                    "theme", user.getTheme() != null ? user.getTheme() : "dark",
                    "font_size", String.valueOf(user.getFontSize() == 0 ? 16 : user.getFontSize()),
                    "font_family", user.getFontFamily() != null ? user.getFontFamily() : "system-ui"
            )));
        });

        app.put("/api/k/settings", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(error("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                User managed = s.get(User.class, user.getId());
                if (body.containsKey("theme")) managed.setTheme((String) body.get("theme"));
                if (body.containsKey("font_size")) managed.setFontSize(Integer.parseInt((String) body.get("font_size")));
                if (body.containsKey("font_family")) managed.setFontFamily((String) body.get("font_family"));
                s.merge(managed);
                s.getTransaction().commit();
            }
            ctx.json(success(Map.of("message", "Settings saved")));
        });
    }

    private static Map<String, Object> success(Object data) { return Map.of("success", true, "data", data); }
    private static Map<String, Object> error(String code, Object msg) { return Map.of("success", false, "error", Map.of("code", code, "message", msg)); }
}
