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

public class SearchRoutes {

    public static void registerRoutes(Javalin app, AuthService authService, MessageService messageService,
                                      ChatService chatService, StoryService storyService,
                                      AdminService adminService) {

        app.get("/api/search", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            String query = ctx.queryParam("q");
            if (query == null || query.isBlank()) { ctx.status(400).json(err("INVALID_INPUT", "Query required")); return; }
            int page = parseIntParam(ctx.queryParam("page"), 1);
            int perPage = Math.min(parseIntParam(ctx.queryParam("per_page"), 50), 100);
            int offset = (page - 1) * perPage;
            String pattern = "%" + query + "%";

            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                var users = listMaps(s,
                    "SELECT id, username, display_name, avatar, status FROM users WHERE username ILIKE :q OR display_name ILIKE :q LIMIT :lim OFFSET :off",
                    "q", pattern, "lim", perPage, "off", offset);
                var chats = listMaps(s,
                    "SELECT c.* FROM chats c JOIN chat_members cm ON cm.chat_id = c.id WHERE cm.user_id = :uid AND (c.title ILIKE :q OR c.description ILIKE :q) LIMIT :lim",
                    "uid", user.getId(), "q", pattern, "lim", perPage);
                var messages = listMaps(s,
                    "SELECT m.* FROM messages m JOIN chat_members cm ON cm.chat_id = m.chat_id WHERE cm.user_id = :uid AND m.content ILIKE :q ORDER BY m.created_at DESC LIMIT :lim OFFSET :off",
                    "uid", user.getId(), "q", pattern, "lim", perPage, "off", offset);
                ctx.json(ok(Map.of("query", query, "users", users, "chats", chats, "messages", messages)));
            }
        });

        app.get("/api/search/users", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            String query = ctx.queryParam("q");
            if (query == null || query.isBlank()) { ctx.status(400).json(err("INVALID_INPUT", "Query required")); return; }
            int perPage = Math.min(parseIntParam(ctx.queryParam("per_page"), 50), 100);
            int page = Math.min(parseIntParam(ctx.queryParam("page"), 1), 100);
            int offset = (page - 1) * perPage;
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                ctx.json(ok(Map.of("query", query, "users", listMaps(s,
                    "SELECT id, username, display_name, avatar, status FROM users WHERE username ILIKE :q OR display_name ILIKE :q LIMIT :lim OFFSET :off",
                    "q", "%" + query + "%", "lim", perPage, "off", offset))));
            }
        });

        app.get("/api/search/messages", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            String query = ctx.queryParam("q");
            if (query == null || query.isBlank()) { ctx.status(400).json(err("INVALID_INPUT", "Query required")); return; }
            int page = parseIntParam(ctx.queryParam("page"), 1);
            int perPage = Math.min(parseIntParam(ctx.queryParam("per_page"), 50), 100);
            int offset = (page - 1) * perPage;
            Long chatId = ctx.queryParam("chat_id") != null ? Long.parseLong(ctx.queryParam("chat_id")) : null;
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                String sql = "SELECT m.* FROM messages m JOIN chat_members cm ON cm.chat_id = m.chat_id WHERE cm.user_id = :uid";
                if (chatId != null) sql += " AND m.chat_id = :cid";
                sql += " AND m.content ILIKE :q ORDER BY m.created_at DESC LIMIT :lim OFFSET :off";
                var q = s.createNativeQuery(sql, Map.class)
                        .setParameter("uid", user.getId()).setParameter("q", "%" + query + "%")
                        .setParameter("lim", perPage).setParameter("off", offset);
                if (chatId != null) q.setParameter("cid", chatId);
                @SuppressWarnings("unchecked")
                var messages = (java.util.List<Map<String, Object>>) (java.util.List) q.list();
                ctx.json(ok(Map.of("query", query, "messages", messages)));
            }
        });
    }

    private static int parseIntParam(String val, int def) {
        if (val == null) return def;
        try { return Integer.parseInt(val); } catch (NumberFormatException e) { return def; }
    }
}
