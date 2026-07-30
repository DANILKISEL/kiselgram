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

public class SavedRoutes {

    public static void registerRoutes(Javalin app, AuthService authService, MessageService messageService,
                                      ChatService chatService, StoryService storyService,
                                      AdminService adminService) {

        app.get("/api/saved_messages", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                ctx.json(ok(listMaps(s,
                    "SELECT m.* FROM messages m JOIN saved_messages sm ON m.id = sm.message_id WHERE sm.user_id = :uid ORDER BY sm.saved_at DESC",
                    "uid", user.getId())));
            }
        });

        app.get("/api/saved", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                ctx.json(ok(listMaps(s,
                    "SELECT sm.*, m.content, m.chat_id FROM saved_messages sm JOIN messages m ON m.id = sm.message_id WHERE sm.user_id = :uid ORDER BY sm.saved_at DESC",
                    "uid", user.getId())));
            }
        });

        app.post("/api/saved", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            Object msgId = body.get("message_id");
            if (msgId == null) { ctx.status(400).json(err("INVALID_INPUT", "message_id required")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery("INSERT INTO saved_messages (user_id, message_id, saved_at) VALUES (:uid, :mid, NOW())")
                        .setParameter("uid", user.getId()).setParameter("mid", ((Number) msgId).longValue()).executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Message saved")));
        });

        app.delete("/api/saved/{messageId}", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            long msgId = ctx.pathParamAsClass("messageId", Long.class).get();
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery("DELETE FROM saved_messages WHERE user_id = :uid AND message_id = :mid")
                        .setParameter("uid", user.getId()).setParameter("mid", msgId).executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Message unsaved")));
        });
    }
}
