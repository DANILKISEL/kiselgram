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

import java.util.Map;

import static ru.kiselgram.web.route.RouteHelper.*;

public class PushRoutes {

    public static void registerRoutes(Javalin app, AuthService authService, MessageService messageService,
                                      ChatService chatService, StoryService storyService,
                                      AdminService adminService) {

        app.post("/api/push/subscribe", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            String endpoint = (String) body.get("endpoint");
            String p256dh = (String) body.get("p256dh");
            String auth = (String) body.get("auth");
            if (endpoint == null) { ctx.status(400).json(err("INVALID_INPUT", "endpoint required")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery("MERGE INTO push_subscriptions (user_id, endpoint, p256dh_key, auth_key, created_at) KEY(endpoint) VALUES (:uid, :ep, :p256, :auth, NOW())")
                        .setParameter("uid", user.getId()).setParameter("ep", endpoint)
                        .setParameter("p256", p256dh != null ? p256dh : "")
                        .setParameter("auth", auth != null ? auth : "").executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Push subscription saved")));
        });

        app.post("/api/push/unsubscribe", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            String endpoint = (String) body.get("endpoint");
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                if (endpoint != null) {
                    s.createNativeMutationQuery("DELETE FROM push_subscriptions WHERE user_id = :uid AND endpoint = :ep")
                            .setParameter("uid", user.getId()).setParameter("ep", endpoint).executeUpdate();
                } else {
                    s.createNativeMutationQuery("DELETE FROM push_subscriptions WHERE user_id = :uid")
                            .setParameter("uid", user.getId()).executeUpdate();
                }
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Push subscription removed")));
        });

        app.get("/api/push/vapid-public-key", ctx -> {
            ctx.json(ok(Map.of("public_key", "BEl62iUYgUivx5kvqEGGm6HrC4FQ0I%2BTqJpO6A5RrVw%2FQxY8%2F4Q9KgJ5iY9L9lLxQfQvP3eZ6a5d4s3a2b1c0d9e8f7g6h5i4j3k2l1m0n9o8p7q6r5s4t3u2v1w0x9y8z7")));
        });
    }
}
