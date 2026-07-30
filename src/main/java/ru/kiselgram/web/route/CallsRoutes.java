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

public class CallsRoutes {

    public static void registerRoutes(Javalin app, AuthService authService, MessageService messageService,
                                      ChatService chatService, StoryService storyService,
                                      AdminService adminService) {

        app.post("/api/calls/start", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            Object calleeId = body.get("callee_id");
            String callType = (String) body.getOrDefault("type", "audio");
            if (calleeId == null) { ctx.status(400).json(err("INVALID_INPUT", "callee_id required")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery(
                    "INSERT INTO calls (caller_id, receiver_id, call_type, status, started_at) VALUES (:cid, :cal, :type, 'ringing', NOW())")
                        .setParameter("cid", user.getId()).setParameter("cal", ((Number) calleeId).longValue())
                        .setParameter("type", callType).executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("status", "ringing", "type", callType)));
        });

        app.post("/api/calls/{callId}/end", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            long callId = ctx.pathParamAsClass("callId", Long.class).get();
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery("UPDATE calls SET status = 'ended', ended_at = NOW() WHERE id = :id AND (caller_id = :uid OR receiver_id = :uid)")
                        .setParameter("id", callId).setParameter("uid", user.getId()).executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Call ended")));
        });

        app.post("/api/calls/{callId}/accept", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            long callId = ctx.pathParamAsClass("callId", Long.class).get();
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery("UPDATE calls SET status = 'active' WHERE id = :id AND receiver_id = :uid")
                        .setParameter("id", callId).setParameter("uid", user.getId()).executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Call accepted")));
        });

        app.get("/api/calls/history", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                ctx.json(ok(listMaps(s,
                    "SELECT c.*, u.username AS caller_name, u2.username AS receiver_name FROM calls c " +
                    "JOIN users u ON u.id = c.caller_id JOIN users u2 ON u2.id = c.receiver_id " +
                    "WHERE c.caller_id = :uid OR c.receiver_id = :uid ORDER BY c.started_at DESC LIMIT 50",
                    "uid", user.getId())));
            }
        });
    }
}
