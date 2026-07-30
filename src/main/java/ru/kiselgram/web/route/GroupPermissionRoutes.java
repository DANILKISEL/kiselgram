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

public class GroupPermissionRoutes {

    public static void registerRoutes(Javalin app, AuthService authService, MessageService messageService,
                                      ChatService chatService, StoryService storyService,
                                      AdminService adminService) {

        app.get("/api/groups/{groupId}/permissions", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            long groupId = ctx.pathParamAsClass("groupId", Long.class).get();
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                var perms = listMaps(s, "SELECT * FROM group_permissions WHERE chat_id = :gid", "gid", groupId);
                if (perms.isEmpty()) {
                    ctx.json(ok(Map.of("send_messages", true, "send_media", true, "add_members", true, "pin_messages", false, "change_info", false)));
                    return;
                }
                ctx.json(ok(perms.get(0)));
            }
        });

        app.post("/api/groups/{groupId}/permissions", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            long groupId = ctx.pathParamAsClass("groupId", Long.class).get();
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                var existing = listMaps(s, "SELECT chat_id FROM group_permissions WHERE chat_id = :gid", "gid", groupId);
                if (existing.isEmpty()) {
                    s.createNativeMutationQuery("INSERT INTO group_permissions (chat_id, can_send_messages, can_send_media, can_add_members, can_pin_messages, can_change_info) VALUES (:gid, :sm, :smed, :am, :pm, :ci)")
                            .setParameter("gid", groupId)
                            .setParameter("sm", body.getOrDefault("send_messages", true))
                            .setParameter("smed", body.getOrDefault("send_media", true))
                            .setParameter("am", body.getOrDefault("add_members", true))
                            .setParameter("pm", body.getOrDefault("pin_messages", false))
                            .setParameter("ci", body.getOrDefault("change_info", false))
                            .executeUpdate();
                } else {
                    s.createNativeMutationQuery("UPDATE group_permissions SET can_send_messages = :sm, can_send_media = :smed, can_add_members = :am, can_pin_messages = :pm, can_change_info = :ci WHERE chat_id = :gid")
                            .setParameter("gid", groupId)
                            .setParameter("sm", body.getOrDefault("send_messages", true))
                            .setParameter("smed", body.getOrDefault("send_media", true))
                            .setParameter("am", body.getOrDefault("add_members", true))
                            .setParameter("pm", body.getOrDefault("pin_messages", false))
                            .setParameter("ci", body.getOrDefault("change_info", false))
                            .executeUpdate();
                }
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Permissions updated")));
        });
    }
}
