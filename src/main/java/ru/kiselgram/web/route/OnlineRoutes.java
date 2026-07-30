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

import static ru.kiselgram.web.route.RouteHelper.*;

public class OnlineRoutes {

    public static void registerRoutes(Javalin app, AuthService authService, MessageService messageService,
                                      ChatService chatService, StoryService storyService,
                                      AdminService adminService) {

        app.post("/api/online/ping", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery("UPDATE users SET last_seen = NOW(), online = true WHERE id = :id")
                        .setParameter("id", user.getId()).executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Pong")));
        });

        app.post("/api/online/offline", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery("UPDATE users SET online = false WHERE id = :id")
                        .setParameter("id", user.getId()).executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Offline")));
        });

        app.get("/api/online/status/{userId}", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            long targetId = ctx.pathParamAsClass("userId", Long.class).get();
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                var rows = listMaps(s, "SELECT id, username, display_name, online, last_seen FROM users WHERE id = :id", "id", targetId);
                if (rows.isEmpty()) { ctx.status(404).json(err("NOT_FOUND", "User not found")); return; }
                Map<String, Object> data = rows.get(0);
                boolean online = data.get("online") != null && Boolean.TRUE.equals(data.get("online"));
                ctx.json(ok(Map.of("user_id", targetId, "online", online, "last_seen", data.get("last_seen"))));
            }
        });

        app.get("/api/online/contacts", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                ctx.json(ok(listMaps(s,
                    "SELECT u.id, u.username, u.display_name, u.avatar, u.last_seen FROM users u " +
                    "JOIN contacts c ON c.contact_id = u.id WHERE c.user_id = :uid AND u.online = true ORDER BY u.last_seen DESC",
                    "uid", user.getId())));
            }
        });
    }
}
