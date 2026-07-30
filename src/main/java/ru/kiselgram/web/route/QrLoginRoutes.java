package ru.kiselgram.web.route;

import ru.kiselgram.web.model.User;
import ru.kiselgram.web.service.AuthService;
import ru.kiselgram.web.service.DatabaseService;
import ru.kiselgram.web.service.MessageService;
import ru.kiselgram.web.service.ChatService;
import ru.kiselgram.web.service.StoryService;
import ru.kiselgram.web.service.AdminService;
import org.hibernate.Session;
import io.javalin.Javalin;

import java.time.LocalDateTime;
import java.util.Map;
import java.util.UUID;
import java.util.function.Supplier;

import static ru.kiselgram.web.route.RouteHelper.*;

public class QrLoginRoutes {

    private static AuthService authService;

    public static void registerRoutes(Javalin app, AuthService as, MessageService messageService,
                                      ChatService chatService, StoryService storyService,
                                      AdminService adminService) {
        authService = as;

        Supplier<String> generateToken = () -> UUID.randomUUID().toString().replace("-", "").substring(0, 16);

        app.post("/api/qr/generate", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            String token = generateToken.get();
            LocalDateTime expiresAt = LocalDateTime.now().plusMinutes(2);
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery("INSERT INTO qr_login_tokens (token, user_id, status, expires_at, created_at) VALUES (:tok, :uid, 'pending', :exp, NOW())")
                        .setParameter("tok", token).setParameter("uid", user.getId()).setParameter("exp", expiresAt).executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("token", token, "expires_in", 120)));
        });

        app.post("/api/auth/qr/generate", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            String token = generateToken.get();
            LocalDateTime expiresAt = LocalDateTime.now().plusMinutes(2);
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery("INSERT INTO qr_login_tokens (token, user_id, status, expires_at, created_at) VALUES (:tok, :uid, 'pending', :exp, NOW())")
                        .setParameter("tok", token).setParameter("uid", user.getId()).setParameter("exp", expiresAt).executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("token", token, "expires_in", 120)));
        });

        app.post("/api/auth/qr/request", ctx -> {
            String token = generateToken.get();
            LocalDateTime expiresAt = LocalDateTime.now().plusMinutes(2);
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery("INSERT INTO qr_login_tokens (token, status, expires_at, created_at) VALUES (:tok, 'pending', :exp, NOW())")
                        .setParameter("tok", token).setParameter("exp", expiresAt).executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("token", token, "expires_in", 120)));
        });

        app.post("/api/auth/qr/authorize", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            String token = (String) body.get("token");
            if (token == null) { ctx.status(400).json(err("INVALID_INPUT", "Token required")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                int updated = s.createNativeMutationQuery("UPDATE qr_login_tokens SET status = 'authorized', user_id = :uid WHERE token = :tok AND status = 'pending' AND expires_at > NOW()")
                        .setParameter("uid", user.getId()).setParameter("tok", token).executeUpdate();
                s.getTransaction().commit();
                if (updated == 0) { ctx.status(400).json(err("INVALID_TOKEN", "Token expired or invalid")); return; }
            }
            ctx.json(ok(Map.of("message", "QR token authorized")));
        });

        app.post("/api/qr/authorize", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            String token = (String) body.get("token");
            if (token == null) { ctx.status(400).json(err("INVALID_INPUT", "Token required")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                int updated = s.createNativeMutationQuery("UPDATE qr_login_tokens SET status = 'authorized', user_id = :uid WHERE token = :tok AND status = 'pending' AND expires_at > NOW()")
                        .setParameter("uid", user.getId()).setParameter("tok", token).executeUpdate();
                s.getTransaction().commit();
                if (updated == 0) { ctx.status(400).json(err("INVALID_TOKEN", "Token expired or invalid")); return; }
            }
            ctx.json(ok(Map.of("message", "QR token authorized")));
        });

        app.post("/api/auth/qr/login", ctx -> {
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            String token = (String) body.get("token");
            if (token == null) { ctx.status(400).json(err("INVALID_INPUT", "Token required")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                var rows = listMaps(s, "SELECT q.user_id, u.username, u.display_name, u.avatar_url FROM qr_login_tokens q JOIN users u ON u.id = q.user_id WHERE q.token = :tok AND q.status = 'authorized' AND q.expires_at > NOW()", "tok", token);
                if (rows.isEmpty()) { ctx.status(400).json(err("INVALID_TOKEN", "Token not authorized or expired")); return; }
                Map<String, Object> row = rows.get(0);
                s.beginTransaction();
                s.createNativeMutationQuery("UPDATE qr_login_tokens SET status = 'used' WHERE token = :tok").setParameter("tok", token).executeUpdate();
                s.getTransaction().commit();
                User qrUser = s.get(User.class, ((Number) row.get("user_id")).longValue());
                String sessionToken = authService.generateToken(qrUser);
                ctx.json(ok(Map.of("session_token", sessionToken, "user", Map.of("user_id", row.get("user_id"), "username", row.get("username"), "display_name", row.get("display_name"), "avatar_url", row.get("avatar_url")))));
            }
        });

        app.get("/api/auth/qr/status/{token}", ctx -> {
            String token = ctx.pathParam("token");
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                var rows = listMaps(s, "SELECT status FROM qr_login_tokens WHERE token = :tok", "tok", token);
                if (rows.isEmpty()) { ctx.status(404).json(err("NOT_FOUND", "Token not found")); return; }
                ctx.json(ok(Map.of("status", rows.get(0).get("status"), "token", token)));
            }
        });

        app.get("/api/qr/check/{token}", ctx -> {
            String token = ctx.pathParam("token");
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                var rows = listMaps(s, "SELECT status FROM qr_login_tokens WHERE token = :tok", "tok", token);
                if (rows.isEmpty()) { ctx.status(404).json(err("NOT_FOUND", "Token not found")); return; }
                ctx.json(ok(Map.of("status", rows.get(0).get("status"), "token", token)));
            }
        });
    }
}
