package ru.kiselgram.web.route;

import ru.kiselgram.web.model.ReadReceipt;
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

public class ReadReceiptRoutes {

    public static void registerRoutes(Javalin app, AuthService authService, MessageService messageService,
                                      ChatService chatService, StoryService storyService,
                                      AdminService adminService) {

        app.get("/api/messages/{msgId}/read_by", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            long msgId = ctx.pathParamAsClass("msgId", Long.class).get();
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                ctx.json(ok(listMaps(s,
                    "SELECT r.user_id, u.username, u.display_name, r.read_at " +
                    "FROM read_receipts r JOIN users u ON u.id = r.user_id " +
                    "WHERE r.message_id = :mid",
                    "mid", msgId)));
            }
        });

        app.post("/api/messages/{msgId}/read", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            long msgId = ctx.pathParamAsClass("msgId", Long.class).get();
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                var existing = s.createQuery("FROM ReadReceipt WHERE messageId = :mid AND userId = :uid", ReadReceipt.class)
                    .setParameter("mid", msgId).setParameter("uid", user.getId()).list();
                if (existing.isEmpty()) {
                    s.persist(new ReadReceipt(msgId, user.getId()));
                }
                s.createNativeMutationQuery("UPDATE messages SET is_read = true, read_at = NOW() WHERE id = :mid AND receiver_id = :uid")
                    .setParameter("mid", msgId).setParameter("uid", user.getId()).executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Marked as read")));
        });
    }
}
