package ru.kiselgram.web.route;

import ru.kiselgram.web.model.Message;
import ru.kiselgram.web.model.User;
import ru.kiselgram.web.repository.MessageRepository;
import ru.kiselgram.web.service.AuthService;
import ru.kiselgram.web.service.MessageService;
import ru.kiselgram.web.service.ChatService;
import ru.kiselgram.web.service.StoryService;
import ru.kiselgram.web.service.AdminService;
import ru.kiselgram.web.service.DatabaseService;
import org.hibernate.Session;
import io.javalin.Javalin;

import java.util.Map;

public class ForwardRoutes {

    private static MessageRepository messageRepo = new MessageRepository();

    public static void registerRoutes(Javalin app, AuthService authService, MessageService messageService,
                                      ChatService chatService, StoryService storyService,
                                      AdminService adminService) {

        app.post("/api/forward", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(error("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            Object msgId = body.get("message_id");
            Object fromChatId = body.get("from_chat_id");
            Object toChatId = body.get("to_chat_id");
            if (msgId == null || toChatId == null) {
                ctx.status(400).json(error("INVALID_INPUT", "message_id and to_chat_id required"));
                return;
            }
            long mid = ((Number) msgId).longValue();
            long toCid = ((Number) toChatId).longValue();
            long fromCid = fromChatId != null ? ((Number) fromChatId).longValue() : 0;

            Message original = messageRepo.findById(mid).orElse(null);
            if (original == null) { ctx.status(404).json(error("NOT_FOUND", "Message not found")); return; }
            Map<String, Object> result = messageService.sendMessage(user.getId(), toCid, original.getContent(), null);
            if (result.containsKey("error")) { ctx.status(400).json(error("FORWARD_FAILED", result.get("error"))); return; }

            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery(
                        "INSERT INTO forwarded_messages (original_message_id, from_chat_id, to_chat_id, forwarded_by, new_message_id, created_at) VALUES (:omid, :fcid, :tcid, :uid, :nmid, NOW())")
                        .setParameter("omid", mid).setParameter("fcid", fromCid)
                        .setParameter("tcid", toCid).setParameter("uid", user.getId())
                        .setParameter("nmid", ((Number) result.get("id")).longValue())
                        .executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(success(Map.of("message", "Message forwarded", "new_message_id", result.get("id"))));
        });

        app.post("/api/forward_messages", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(error("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            Object toChatId = body.get("to_chat_id");
            Object messageIds = body.get("message_ids");
            if (toChatId == null || messageIds == null) {
                ctx.status(400).json(error("INVALID_INPUT", "to_chat_id and message_ids required"));
                return;
            }
            long toCid = ((Number) toChatId).longValue();
            java.util.List<Integer> ids = (java.util.List<Integer>) messageIds;
            int count = 0;
            for (Number id : ids) {
                Message original = messageRepo.findById(id.longValue()).orElse(null);
                if (original == null) continue;
                Map<String, Object> result = messageService.sendMessage(user.getId(), toCid, original.getContent(), null);
                if (!result.containsKey("error")) count++;
            }
            ctx.json(success(Map.of("message", count + " messages forwarded", "count", count)));
        });
    }

    private static Map<String, Object> success(Object data) { return Map.of("success", true, "data", data); }
    private static Map<String, Object> error(String code, Object msg) { return Map.of("success", false, "error", Map.of("code", code, "message", msg)); }
}
