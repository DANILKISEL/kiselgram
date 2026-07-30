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

public class MessagePinRoutes {

    public static void registerRoutes(Javalin app, AuthService authService, MessageService messageService,
                                      ChatService chatService, StoryService storyService,
                                      AdminService adminService) {

        app.post("/api/messages/pin", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            Object msgId = body.get("message_id");
            Object chatId = body.get("chat_id");
            if (msgId == null || chatId == null) { ctx.status(400).json(err("INVALID_INPUT", "message_id and chat_id required")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                var existing = listMaps(s, "SELECT id FROM pins WHERE chat_id = :cid AND pinned_by = :uid AND message_id = :mid", "cid", ((Number) chatId).longValue(), "uid", user.getId(), "mid", ((Number) msgId).longValue());
                if (existing.isEmpty()) {
                    s.createNativeMutationQuery("INSERT INTO pins (chat_id, pinned_by, message_id, pinned_at) VALUES (:cid, :uid, :mid, NOW())")
                            .setParameter("cid", ((Number) chatId).longValue()).setParameter("uid", user.getId()).setParameter("mid", ((Number) msgId).longValue()).executeUpdate();
                } else {
                    s.createNativeMutationQuery("DELETE FROM pins WHERE id = :id").setParameter("id", existing.get(0).get("id")).executeUpdate();
                }
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Message pin toggled")));
        });

        app.get("/api/messages/pinned", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            String chatIdStr = ctx.queryParam("chat_id");
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                if (chatIdStr != null) {
                    ctx.json(ok(listMaps(s, "SELECT p.*, m.content, m.sender_id, u.username AS sender_name FROM pins p JOIN messages m ON m.id = p.message_id JOIN users u ON u.id = m.sender_id WHERE p.chat_id = :cid ORDER BY p.pinned_at DESC", "cid", Long.parseLong(chatIdStr))));
                } else {
                    ctx.json(ok(listMaps(s, "SELECT p.*, m.content, m.sender_id, u.username AS sender_name FROM pins p JOIN messages m ON m.id = p.message_id JOIN users u ON u.id = m.sender_id WHERE p.pinned_by = :uid ORDER BY p.pinned_at DESC", "uid", user.getId())));
                }
            }
        });

        app.post("/api/messages/pinned/dismiss", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            Object chatId = body.get("chat_id");
            if (chatId == null) { ctx.status(400).json(err("INVALID_INPUT", "chat_id required")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery("DELETE FROM pins WHERE chat_id = :cid AND pinned_by = :uid")
                        .setParameter("cid", ((Number) chatId).longValue()).setParameter("uid", user.getId()).executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Pinned messages dismissed")));
        });
    }
}
