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

import static ru.kiselgram.web.route.RouteHelper.*;

public class ReferralRoutes {

    public static void registerRoutes(Javalin app, AuthService authService, MessageService messageService,
                                      ChatService chatService, StoryService storyService,
                                      AdminService adminService) {

        app.get("/api/referrals/info", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                var rows = listMaps(s, "SELECT code FROM referrals WHERE referrer_id = :uid LIMIT 1", "uid", user.getId());
                String code = rows.isEmpty() ? UUID.randomUUID().toString().substring(0, 8) : (String) rows.get(0).get("code");
                if (rows.isEmpty()) {
                    s.beginTransaction();
                    s.createNativeMutationQuery("INSERT INTO referrals (referrer_id, code, created_at) VALUES (:uid, :code, NOW())")
                            .setParameter("uid", user.getId()).setParameter("code", code).executeUpdate();
                    s.getTransaction().commit();
                }
                var countRows = listMaps(s, "SELECT COUNT(*) AS cnt FROM referrals WHERE referrer_id = :uid AND status = 'active'", "uid", user.getId());
                long count = countRows.isEmpty() ? 0 : ((Number) countRows.get(0).get("cnt")).longValue();
                ctx.json(ok(Map.of("count", count, "code", code, "link", "/join?ref=" + code, "premium", count >= 10)));
            }
        });

        app.get("/api/referrals/list", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                ctx.json(ok(listMaps(s,
                    "SELECT r.*, u.username, u.display_name FROM referrals r JOIN users u ON u.id = r.referred_id WHERE r.referrer_id = :uid ORDER BY r.created_at DESC",
                    "uid", user.getId())));
            }
        });

        app.get("/api/referrals", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                ctx.json(ok(listMaps(s, "SELECT r.*, u.username, u.display_name FROM referrals r JOIN users u ON u.id = r.referred_id WHERE r.referrer_id = :uid", "uid", user.getId())));
            }
        });

        app.post("/api/referrals/claim", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                var countRows = listMaps(s, "SELECT COUNT(*) AS cnt FROM referrals WHERE referrer_id = :uid AND status = 'active'", "uid", user.getId());
                long count = countRows.isEmpty() ? 0 : ((Number) countRows.get(0).get("cnt")).longValue();
                if (count < 10) { ctx.status(400).json(err("NOT_ENOUGH", "Need 10 referrals for premium")); return; }
                s.beginTransaction();
                LocalDateTime exp = LocalDateTime.now().plusMonths(1);
                s.createNativeMutationQuery("MERGE INTO user_premium (user_id, is_premium, premium_plan, premium_since, premium_expires_at, premium_auto_renew) KEY(user_id) VALUES (:uid, true, 'referral', NOW(), :exp, false)")
                        .setParameter("exp", exp)
                        .setParameter("uid", user.getId()).executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Referral bonus claimed")));
        });
    }
}
