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

import static ru.kiselgram.web.route.RouteHelper.*;

public class PremiumRoutes {

    public static void registerRoutes(Javalin app, AuthService authService, MessageService messageService,
                                      ChatService chatService, StoryService storyService,
                                      AdminService adminService) {

        app.get("/api/premium/status", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                var rows = listMaps(s, "SELECT is_premium, premium_plan, premium_expires_at, premium_auto_renew FROM user_premium WHERE user_id = :uid", "uid", user.getId());
                if (rows.isEmpty()) { ctx.json(ok(Map.of("is_premium", false, "plan", "none"))); return; }
                Map<String, Object> row = rows.get(0);
                ctx.json(ok(Map.of("is_premium", row.get("is_premium"), "plan", row.getOrDefault("premium_plan", "none"), "expires_at", row.get("premium_expires_at"), "auto_renew", row.get("premium_auto_renew"))));
            }
        });

        app.post("/api/premium/subscribe", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            String plan = (String) body.getOrDefault("plan", "monthly");
            LocalDateTime expiresAt = LocalDateTime.now().plusMonths(plan.equals("yearly") ? 12 : 1);
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                var existing = listMaps(s, "SELECT user_id FROM user_premium WHERE user_id = :uid", "uid", user.getId());
                if (existing.isEmpty()) {
                    s.createNativeMutationQuery("INSERT INTO user_premium (user_id, is_premium, premium_plan, premium_since, premium_expires_at, premium_auto_renew) VALUES (:uid, true, :plan, NOW(), :exp, true)")
                            .setParameter("uid", user.getId()).setParameter("plan", plan).setParameter("exp", expiresAt).executeUpdate();
                } else {
                    s.createNativeMutationQuery("UPDATE user_premium SET is_premium = true, premium_plan = :plan, premium_since = COALESCE(premium_since, NOW()), premium_expires_at = :exp, premium_auto_renew = true WHERE user_id = :uid")
                            .setParameter("uid", user.getId()).setParameter("plan", plan).setParameter("exp", expiresAt).executeUpdate();
                }
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Subscribed to premium", "plan", plan)));
        });

        app.post("/api/premium/cancel", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery("UPDATE user_premium SET premium_auto_renew = false WHERE user_id = :uid")
                        .setParameter("uid", user.getId()).executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Auto-renewal cancelled")));
        });
    }
}
