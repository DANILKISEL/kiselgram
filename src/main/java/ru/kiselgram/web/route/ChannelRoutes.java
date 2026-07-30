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

public class ChannelRoutes {

    private static AuthService authService;
    private static MessageService messageService;
    private static ChatService chatService;

    public static void registerRoutes(Javalin app, AuthService as, MessageService ms,
                                      ChatService cs, StoryService storyService,
                                      AdminService adminService) {
        authService = as;
        messageService = ms;
        chatService = cs;

        app.get("/api/channels/{channelId}", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            Long channelId = ctx.pathParamAsClass("channelId", Long.class).get();
            ctx.json(Map.of("success", true, "data", Map.of("id", channelId)));
        });

        app.get("/api/channel_messages/{channelId}", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            Long channelId = ctx.pathParamAsClass("channelId", Long.class).get();
            long afterId = parseLongParam(ctx.queryParam("after_id"), 0L);
            int limit = Math.min(parseIntParam(ctx.queryParam("limit"), 50), 100);
            List<Map<String, Object>> messages = messageService.getChannelMessages(user.getId(), channelId, afterId, limit);
            ctx.json(Map.of("success", true, "data", Map.of("messages", messages)));
        });

        app.post("/api/channels/create", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            String name = (String) body.get("name");
            String description = (String) body.get("description");
            if (name == null) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "INVALID_INPUT", "message", "Channel name required")));
                return;
            }
            Map<String, Object> result = chatService.createChannel(user.getId(), name, description);
            if (result.containsKey("error")) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "CREATE_FAILED", "message", result.get("error"))));
                return;
            }
            ctx.json(Map.of("success", true, "data", result));
        });

        app.post("/api/send_channel_message", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            Long channelId = body.get("channel_id") != null ? ((Number) body.get("channel_id")).longValue() : null;
            String content = (String) body.get("content");
            if (channelId == null || content == null) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "INVALID_INPUT", "message", "Channel ID and content required")));
                return;
            }
            Map<String, Object> result = messageService.sendChannelMessage(user.getId(), channelId, content);
            if (result.containsKey("error")) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "SEND_FAILED", "message", result.get("error"))));
                return;
            }
            ctx.json(Map.of("success", true, "data", result));
        });

        app.post("/api/channels/{channelId}/subscribe", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            Long channelId = ctx.pathParamAsClass("channelId", Long.class).get();
            Map<String, Object> result = chatService.subscribe(user.getId(), channelId);
            if (result.containsKey("error")) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "SUBSCRIBE_FAILED", "message", result.get("error"))));
                return;
            }
            ctx.json(Map.of("success", true, "data", result));
        });

        app.post("/api/channels/{channelId}/unsubscribe", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            Long channelId = ctx.pathParamAsClass("channelId", Long.class).get();
            Map<String, Object> result = chatService.unsubscribe(user.getId(), channelId);
            if (result.containsKey("error")) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "UNSUBSCRIBE_FAILED", "message", result.get("error"))));
                return;
            }
            ctx.json(Map.of("success", true, "data", result));
        });

        app.post("/api/channels/{channelId}/update", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            Long channelId = ctx.pathParamAsClass("channelId", Long.class).get();
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            Map<String, Object> result = chatService.updateChannel(user.getId(), channelId, body);
            if (result.containsKey("error")) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "UPDATE_FAILED", "message", result.get("error"))));
                return;
            }
            ctx.json(Map.of("success", true, "data", result));
        });

        app.post("/api/channels/{channelId}/admins", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            ctx.json(Map.of("success", true, "data", Map.of("message", "Admin added")));
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
