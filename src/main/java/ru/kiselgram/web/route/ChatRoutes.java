package ru.kiselgram.web.route;

import ru.kiselgram.web.model.User;
import ru.kiselgram.web.service.AuthService;
import ru.kiselgram.web.service.MessageService;
import ru.kiselgram.web.service.ChatService;
import ru.kiselgram.web.service.StoryService;
import ru.kiselgram.web.service.AdminService;
import ru.kiselgram.web.util.Helpers;
import io.javalin.Javalin;
import io.javalin.http.Context;

import java.util.List;
import java.util.Map;

public class ChatRoutes {

    public static void registerRoutes(Javalin app, AuthService authService, MessageService messageService,
                                      ChatService chatService, StoryService storyService,
                                      AdminService adminService) {

        app.get("/api/chat_list", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            int page = parseIntParam(ctx.queryParam("page"), 1);
            int perPage = Math.min(parseIntParam(ctx.queryParam("per_page"), 50), 100);
            List<Map<String, Object>> chats = chatService.getChatList(user.getId(), page, perPage);
            ctx.json(Map.of("success", true, "data", Map.of("chats", chats, "page", page, "per_page", perPage)));
        });

        app.get("/api/messages/{userId}", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            Long peerId = ctx.pathParamAsClass("userId", Long.class).get();
            long afterId = parseLongParam(ctx.queryParam("after_id"), 0L);
            int limit = Math.min(parseIntParam(ctx.queryParam("limit"), 50), 100);
            List<Map<String, Object>> messages = messageService.getMessages(user.getId(), peerId, afterId, limit);
            ctx.json(Map.of("success", true, "data", Map.of("messages", messages, "after_id", afterId, "limit", limit)));
        });

        app.get("/api/bot/{botId}/webapp", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            Long botId = ctx.pathParamAsClass("botId", Long.class).get();
            ctx.json(Map.of("success", true, "data", Map.of("bot_id", botId, "webapp_url", "")));
        });

        app.put("/api/bot/{botId}/webapp", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            ctx.json(Map.of("success", true, "data", Map.of("message", "Bot webapp URL updated")));
        });

        app.get("/api/bots", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            ctx.json(Map.of("success", true, "data", List.of()));
        });

        app.post("/api/bots", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            ctx.json(Map.of("success", true, "data", Map.of("message", "Bot created")));
        });
    }

    private static int parseIntParam(String val, int def) {
        if (val == null) return def;
        try { return Integer.parseInt(val); } catch (NumberFormatException e) { return def; }
    }

    private static long parseLongParam(String val, long def) {
        if (val == null) return def;
        try { return Long.parseLong(val); } catch (NumberFormatException e) { return def; }
    }
}
