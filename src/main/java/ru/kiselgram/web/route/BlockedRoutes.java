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

public class BlockedRoutes {

    public static void registerRoutes(Javalin app, AuthService authService, MessageService messageService,
                                      ChatService chatService, StoryService storyService,
                                      AdminService adminService) {

        app.get("/api/blocked", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                ctx.json(ok(listMaps(s,
                    "SELECT b.*, u.username, u.display_name, u.avatar FROM blocked_users b JOIN users u ON u.id = b.blocked_id WHERE b.user_id = :uid ORDER BY b.created_at DESC",
                    "uid", user.getId())));
            }
        });

        app.post("/api/blocked", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            Object blockedId = body.get("user_id");
            if (blockedId == null) { ctx.status(400).json(err("INVALID_INPUT", "user_id required")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery("INSERT INTO blocked_users (user_id, blocked_id, created_at) VALUES (:uid, :bid, NOW()) ON CONFLICT DO NOTHING")
                        .setParameter("uid", user.getId()).setParameter("bid", ((Number) blockedId).longValue()).executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "User blocked")));
        });

        app.delete("/api/blocked/{userId}", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            long blockedId = ctx.pathParamAsClass("userId", Long.class).get();
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery("DELETE FROM blocked_users WHERE user_id = :uid AND blocked_id = :bid")
                        .setParameter("uid", user.getId()).setParameter("bid", blockedId).executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "User unblocked")));
        });
    }
}
