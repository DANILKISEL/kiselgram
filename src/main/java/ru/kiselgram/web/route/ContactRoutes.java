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

public class ContactRoutes {

    private static AuthService authService;
    private static ChatService chatService;

    public static void registerRoutes(Javalin app, AuthService as, MessageService messageService,
                                      ChatService cs, StoryService storyService,
                                      AdminService adminService) {
        authService = as;
        chatService = cs;

        app.get("/api/contacts", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                ctx.json(ok(listMaps(s,
                    "SELECT c.id AS contact_id, u.id, u.username, u.display_name, u.avatar_url, u.bio, u.is_online, c.custom_name, c.created_at " +
                    "FROM contacts c JOIN users u ON u.id = c.contact_id WHERE c.user_id = :uid ORDER BY c.created_at DESC",
                    "uid", user.getId())));
            }
        });

        app.post("/api/contacts", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            Long contactId = body.get("contact_id") != null ? ((Number) body.get("contact_id")).longValue() : null;
            if (contactId == null) { ctx.status(400).json(err("INVALID_INPUT", "Contact ID required")); return; }
            Map<String, Object> result = chatService.addContact(user.getId(), contactId);
            if (result.containsKey("error")) { ctx.status(400).json(err("ADD_FAILED", result.get("error"))); return; }
            ctx.json(ok(result));
        });

        app.post("/api/contacts/rename", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            Object contactId = body.get("contact_id");
            String customName = (String) body.get("custom_name");
            if (contactId == null) { ctx.status(400).json(err("INVALID_INPUT", "contact_id required")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery("UPDATE contacts SET custom_name = :name WHERE user_id = :uid AND contact_id = :cid")
                        .setParameter("uid", user.getId()).setParameter("cid", ((Number) contactId).longValue())
                        .setParameter("name", customName).executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Contact renamed")));
        });

        app.delete("/api/contacts/{contactId}", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Long contactId = ctx.pathParamAsClass("contactId", Long.class).get();
            Map<String, Object> result = chatService.removeContact(user.getId(), contactId);
            if (result.containsKey("error")) { ctx.status(400).json(err("REMOVE_FAILED", result.get("error"))); return; }
            ctx.json(ok(result));
        });

        app.get("/api/blocked_users", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                ctx.json(ok(listMaps(s,
                    "SELECT b.*, u.username, u.display_name, u.avatar_url FROM blocked_users b JOIN users u ON u.id = b.blocked_user_id WHERE b.user_id = :uid ORDER BY b.created_at DESC",
                    "uid", user.getId())));
            }
        });

        app.post("/api/block_user/{userId}", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Long blockedId = ctx.pathParamAsClass("userId", Long.class).get();
            Map<String, Object> result = chatService.blockUser(user.getId(), blockedId);
            if (result.containsKey("error")) { ctx.status(400).json(err("BLOCK_FAILED", result.get("error"))); return; }
            ctx.json(ok(result));
        });

        app.post("/api/unblock_user/{userId}", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Long blockedId = ctx.pathParamAsClass("userId", Long.class).get();
            Map<String, Object> result = chatService.unblockUser(user.getId(), blockedId);
            if (result.containsKey("error")) { ctx.status(400).json(err("UNBLOCK_FAILED", result.get("error"))); return; }
            ctx.json(ok(result));
        });
    }
}
