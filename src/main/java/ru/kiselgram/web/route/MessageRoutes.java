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

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class MessageRoutes {

    private static final Map<String, Map<Long, List<String>>> typingStatus = new ConcurrentHashMap<>();

    public static void registerRoutes(Javalin app, AuthService authService, MessageService messageService,
                                      ChatService chatService, StoryService storyService,
                                      AdminService adminService) {

        app.post("/api/send_message", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            Long receiverId = body.get("receiver_id") != null ? ((Number) body.get("receiver_id")).longValue() : null;
            String content = (String) body.get("content");
            Long replyToId = body.get("reply_to_id") != null ? ((Number) body.get("reply_to_id")).longValue() : null;
            if (receiverId == null || content == null) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "INVALID_INPUT", "message", "Receiver and content required")));
                return;
            }
            Map<String, Object> result = messageService.sendMessage(user.getId(), receiverId, content, replyToId);
            if (result.containsKey("error")) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "SEND_FAILED", "message", result.get("error"))));
                return;
            }
            ctx.json(Map.of("success", true, "data", result));
        });

        app.post("/api/mark_read/{userId}", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            Long peerId = ctx.pathParamAsClass("userId", Long.class).get();
            messageService.markRead(user.getId(), peerId);
            ctx.json(Map.of("success", true, "data", Map.of("message", "Marked as read")));
        });

        app.post("/api/messages/{messageId}/edit", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            Long messageId = ctx.pathParamAsClass("messageId", Long.class).get();
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            String content = (String) body.get("content");
            if (content == null) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "INVALID_INPUT", "message", "Content required")));
                return;
            }
            Map<String, Object> result = messageService.editMessage(user.getId(), messageId, content);
            if (result.containsKey("error")) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "EDIT_FAILED", "message", result.get("error"))));
                return;
            }
            ctx.json(Map.of("success", true, "data", result));
        });

        app.post("/api/typing/{chatType}/{chatId}", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            String chatType = ctx.pathParam("chatType");
            Long chatId = ctx.pathParamAsClass("chatId", Long.class).get();
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            String action = (String) body.get("action");
            String key = chatType + "_" + chatId;
            typingStatus.putIfAbsent(key, new ConcurrentHashMap<>());
            Map<Long, List<String>> chatTyping = typingStatus.get(key);
            if ("typing".equals(action)) {
                chatTyping.computeIfAbsent(user.getId(), k -> new ArrayList<>()).add("typing");
            } else {
                chatTyping.remove(user.getId());
            }
            ctx.json(Map.of("success", true));
        });

        app.get("/api/typing/{chatType}/{chatId}", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            String chatType = ctx.pathParam("chatType");
            Long chatId = ctx.pathParamAsClass("chatId", Long.class).get();
            String key = chatType + "_" + chatId;
            Map<Long, List<String>> chatTyping = typingStatus.getOrDefault(key, new ConcurrentHashMap<>());
            List<Map<String, Object>> result = new ArrayList<>();
            for (Map.Entry<Long, List<String>> entry : chatTyping.entrySet()) {
                Map<String, Object> item = new HashMap<>();
                item.put("user_id", entry.getKey());
                item.put("actions", entry.getValue());
                result.add(item);
            }
            ctx.json(Map.of("success", true, "data", result));
        });

        app.post("/api/reactions/add", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            Long messageId = body.get("message_id") != null ? ((Number) body.get("message_id")).longValue() : null;
            String type = (String) body.get("type");
            if (messageId == null || type == null) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "INVALID_INPUT", "message", "Message ID and type required")));
                return;
            }
            Map<String, Object> result = messageService.addReaction(user.getId(), messageId, type);
            if (result.containsKey("error")) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "REACTION_FAILED", "message", result.get("error"))));
                return;
            }
            ctx.json(Map.of("success", true, "data", result));
        });

        app.get("/api/reactions/{messageId}", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            Long messageId = ctx.pathParamAsClass("messageId", Long.class).get();
            List<Map<String, Object>> reactions = messageService.getReactions(messageId);
            ctx.json(Map.of("success", true, "data", reactions));
        });

        app.post("/api/messages/{messageId}/delete", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            Long messageId = ctx.pathParamAsClass("messageId", Long.class).get();
            Map<String, Object> result = messageService.deleteMessage(user.getId(), messageId);
            if (result.containsKey("error")) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "DELETE_FAILED", "message", result.get("error"))));
                return;
            }
            ctx.json(Map.of("success", true, "data", result));
        });
    }
}
