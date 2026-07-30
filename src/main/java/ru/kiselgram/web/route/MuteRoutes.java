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

public class MuteRoutes {

    public static void registerRoutes(Javalin app, AuthService authService, MessageService messageService,
                                      ChatService chatService, StoryService storyService,
                                      AdminService adminService) {

        app.get("/api/muted", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                ctx.json(ok(listMaps(s,
                    "SELECT mc.*, c.title FROM muted_chats mc JOIN chats c ON c.id = mc.chat_id WHERE mc.user_id = :uid ORDER BY mc.created_at DESC",
                    "uid", user.getId())));
            }
        });

        app.post("/api/muted", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            Object chatId = body.get("chat_id");
            if (chatId == null) { ctx.status(400).json(err("INVALID_INPUT", "chat_id required")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery("INSERT INTO muted_chats (user_id, chat_id, created_at) VALUES (:uid, :cid, NOW()) ON CONFLICT DO NOTHING")
                        .setParameter("uid", user.getId()).setParameter("cid", ((Number) chatId).longValue()).executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Chat muted")));
        });

        app.delete("/api/muted", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            Object chatId = body.get("chat_id");
            if (chatId == null) { ctx.status(400).json(err("INVALID_INPUT", "chat_id required")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery("DELETE FROM muted_chats WHERE user_id = :uid AND chat_id = :cid")
                        .setParameter("uid", user.getId()).setParameter("cid", ((Number) chatId).longValue()).executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Chat unmuted")));
        });
    }
}
