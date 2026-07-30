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

public class ReportRoutes {

    public static void registerRoutes(Javalin app, AuthService authService, MessageService messageService,
                                      ChatService chatService, StoryService storyService,
                                      AdminService adminService) {

        app.post("/api/report", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            String type = (String) body.get("type");
            Object targetId = body.get("target_id");
            String reason = (String) body.get("reason");
            if (type == null || targetId == null) { ctx.status(400).json(err("INVALID_INPUT", "type and target_id required")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery(
                    "INSERT INTO reports (reporter_id, target_type, target_id, reason, status, created_at) VALUES (:uid, :type, :tid, :reason, 'open', NOW())")
                        .setParameter("uid", user.getId()).setParameter("type", type)
                        .setParameter("tid", ((Number) targetId).longValue())
                        .setParameter("reason", reason != null ? reason : "").executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Report submitted")));
        });

        app.get("/api/reports", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null || !user.isAdmin()) { ctx.status(403).json(err("FORBIDDEN", "Admin only")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                ctx.json(ok(listMaps(s,
                    "SELECT r.*, u.username AS reporter_name FROM reports r JOIN users u ON u.id = r.reporter_id ORDER BY r.created_at DESC")));
            }
        });

        app.post("/api/reports/{reportId}/resolve", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null || !user.isAdmin()) { ctx.status(403).json(err("FORBIDDEN", "Admin only")); return; }
            long reportId = ctx.pathParamAsClass("reportId", Long.class).get();
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery("UPDATE reports SET status = 'resolved' WHERE id = :id")
                        .setParameter("id", reportId).executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Report resolved")));
        });
    }
}
