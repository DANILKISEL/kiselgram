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
import java.util.UUID;

import static ru.kiselgram.web.route.RouteHelper.*;

public class InviteLinkRoutes {

    public static void registerRoutes(Javalin app, AuthService authService, MessageService messageService,
                                      ChatService chatService, StoryService storyService,
                                      AdminService adminService) {

        app.get("/api/groups/{chatId}/invites", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            long chatId = ctx.pathParamAsClass("chatId", Long.class).get();
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                ctx.json(ok(listMaps(s, "SELECT * FROM invite_links WHERE chat_id = :cid ORDER BY created_at DESC", "cid", chatId)));
            }
        });

        app.post("/api/groups/{chatId}/invites/create", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            long chatId = ctx.pathParamAsClass("chatId", Long.class).get();
            String code = UUID.randomUUID().toString().replace("-", "").substring(0, 12);
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery("INSERT INTO invite_links (chat_id, code, created_by, created_at, expires_at, max_uses, use_count) VALUES (:cid, :code, :uid, NOW(), NULL, 0, 0)")
                        .setParameter("cid", chatId).setParameter("code", code).setParameter("uid", user.getId()).executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("code", code, "link", "/join_group/" + code)));
        });

        app.post("/api/groups/{chatId}/invites/revoke", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            long chatId = ctx.pathParamAsClass("chatId", Long.class).get();
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            String code = (String) body.get("code");
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery("DELETE FROM invite_links WHERE chat_id = :cid AND code = :code")
                        .setParameter("cid", chatId).setParameter("code", code).executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Invite link revoked")));
        });
    }
}
