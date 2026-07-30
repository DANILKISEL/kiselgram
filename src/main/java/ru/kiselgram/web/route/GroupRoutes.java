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

import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class GroupRoutes {

    private static AuthService authService;
    private static MessageService messageService;
    private static ChatService chatService;

    public static void registerRoutes(Javalin app, AuthService as, MessageService ms,
                                      ChatService cs, StoryService storyService,
                                      AdminService adminService) {
        authService = as;
        messageService = ms;
        chatService = cs;

        app.get("/api/groups", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            ctx.json(Map.of("success", true, "data", List.of()));
        });

        app.get("/api/groups/{groupId}", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            Long groupId = ctx.pathParamAsClass("groupId", Long.class).get();
            ctx.json(Map.of("success", true, "data", Map.of("id", groupId)));
        });

        app.get("/api/groups/{groupId}/members", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            Long groupId = ctx.pathParamAsClass("groupId", Long.class).get();
            int page = parseIntParam(ctx.queryParam("page"), 1);
            int perPage = Math.min(parseIntParam(ctx.queryParam("per_page"), 50), 100);
            List<Map<String, Object>> members = chatService.getGroupMembers(groupId, page, perPage)
                    .stream().map(m -> m.toMap()).toList();
            ctx.json(Map.of("success", true, "data", Map.of("members", members)));
        });

        app.get("/api/group_messages/{groupId}", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            Long groupId = ctx.pathParamAsClass("groupId", Long.class).get();
            long afterId = parseLongParam(ctx.queryParam("after_id"), 0L);
            int limit = Math.min(parseIntParam(ctx.queryParam("limit"), 50), 100);
            List<Map<String, Object>> messages = messageService.getGroupMessages(user.getId(), groupId, afterId, limit);
            ctx.json(Map.of("success", true, "data", Map.of("messages", messages)));
        });

        app.post("/api/groups/create", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            String name = (String) body.get("name");
            String description = (String) body.get("description");
            List<Long> memberIds = body.get("member_ids") != null
                    ? ((List<Number>) body.get("member_ids")).stream().map(Number::longValue).toList()
                    : null;
            if (name == null) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "INVALID_INPUT", "message", "Group name required")));
                return;
            }
            Map<String, Object> result = chatService.createGroup(user.getId(), name, description, memberIds);
            if (result.containsKey("error")) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "CREATE_FAILED", "message", result.get("error"))));
                return;
            }
            ctx.json(Map.of("success", true, "data", result));
        });

        app.post("/api/send_group_message", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            Long groupId = body.get("group_id") != null ? ((Number) body.get("group_id")).longValue() : null;
            String content = (String) body.get("content");
            Long replyToId = body.get("reply_to_id") != null ? ((Number) body.get("reply_to_id")).longValue() : null;
            if (groupId == null || content == null) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "INVALID_INPUT", "message", "Group ID and content required")));
                return;
            }
            Map<String, Object> result = messageService.sendGroupMessage(user.getId(), groupId, content, replyToId);
            if (result.containsKey("error")) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "SEND_FAILED", "message", result.get("error"))));
                return;
            }
            ctx.json(Map.of("success", true, "data", result));
        });

        app.post("/api/groups/{groupId}/update", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            Long groupId = ctx.pathParamAsClass("groupId", Long.class).get();
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            Map<String, Object> result = chatService.updateGroup(user.getId(), groupId, body);
            if (result.containsKey("error")) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "UPDATE_FAILED", "message", result.get("error"))));
                return;
            }
            ctx.json(Map.of("success", true, "data", result));
        });

        app.post("/api/groups/{groupId}/members/{userId}/role", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            ctx.json(Map.of("success", true, "data", Map.of("message", "Role updated")));
        });

        app.get("/api/join_group/{inviteLink}", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            String inviteLink = ctx.pathParam("inviteLink");
            Map<String, Object> result = chatService.joinGroup(user.getId(), inviteLink);
            if (result.containsKey("error")) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "JOIN_FAILED", "message", result.get("error"))));
                return;
            }
            ctx.json(Map.of("success", true, "data", result));
        });

        app.post("/api/leave_group/{groupId}", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            Long groupId = ctx.pathParamAsClass("groupId", Long.class).get();
            Map<String, Object> result = chatService.leaveGroup(user.getId(), groupId);
            if (result.containsKey("error")) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "LEAVE_FAILED", "message", result.get("error"))));
                return;
            }
            ctx.json(Map.of("success", true, "data", result));
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
