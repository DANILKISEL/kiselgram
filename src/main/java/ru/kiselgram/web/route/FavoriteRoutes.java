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

import java.util.List;
import java.util.Map;

import static ru.kiselgram.web.route.RouteHelper.*;

public class FavoriteRoutes {

    public static void registerRoutes(Javalin app, AuthService authService, MessageService messageService,
                                      ChatService chatService, StoryService storyService,
                                      AdminService adminService) {

        app.get("/api/favorites", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                ctx.json(ok(listMaps(s,
                    "SELECT f.*, u.username, u.avatar FROM favorites f JOIN users u ON u.id = f.target_id WHERE f.user_id = :uid ORDER BY f.created_at DESC",
                    "uid", user.getId())));
            }
        });

        app.post("/api/favorites", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            Object targetId = body.get("target_id");
            String type = (String) body.getOrDefault("type", "user");
            if (targetId == null) { ctx.status(400).json(err("INVALID_INPUT", "target_id required")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery("INSERT INTO favorites (user_id, target_id, type, created_at) VALUES (:uid, :tid, :type, NOW()) ON CONFLICT DO NOTHING")
                        .setParameter("uid", user.getId()).setParameter("tid", ((Number) targetId).longValue())
                        .setParameter("type", type).executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Favorite added")));
        });

        app.delete("/api/favorites/{favoriteId}", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            long favId = ctx.pathParamAsClass("favoriteId", Long.class).get();
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery("DELETE FROM favorites WHERE id = :id AND user_id = :uid")
                        .setParameter("id", favId).setParameter("uid", user.getId()).executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Favorite removed")));
        });
    }
}
