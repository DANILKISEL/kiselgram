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

public class StoryRoutes {

    private static AuthService authService;
    private static StoryService storyService;

    public static void registerRoutes(Javalin app, AuthService as, MessageService messageService,
                                      ChatService chatService, StoryService ss,
                                      AdminService adminService) {
        authService = as;
        storyService = ss;

        app.post("/api/stories/create", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            String mediaPath = (String) body.get("media_path");
            String mediaType = (String) body.get("media_type");
            String caption = (String) body.get("caption");
            if (mediaPath == null || mediaType == null) { ctx.status(400).json(err("INVALID_INPUT", "Media path and type required")); return; }
            Map<String, Object> result = storyService.createStory(user.getId(), mediaPath, mediaType, caption);
            if (result.containsKey("error")) { ctx.status(400).json(err("CREATE_FAILED", result.get("error"))); return; }
            ctx.json(ok(result));
        });

        app.get("/api/stories", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> result = storyService.getActiveStories(user.getId());
            if (result.containsKey("error")) { ctx.status(400).json(err("FETCH_FAILED", result.get("error"))); return; }
            ctx.json(ok(result));
        });

        app.post("/api/stories/{storyId}/view", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Long storyId = ctx.pathParamAsClass("storyId", Long.class).get();
            Map<String, Object> result = storyService.viewStory(storyId, user.getId());
            if (result.containsKey("error")) { ctx.status(400).json(err("VIEW_FAILED", result.get("error"))); return; }
            ctx.json(ok(result));
        });

        app.post("/api/stories/{storyId}/like", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Long storyId = ctx.pathParamAsClass("storyId", Long.class).get();
            Map<String, Object> result = storyService.likeStory(storyId, user.getId());
            if (result.containsKey("error")) { ctx.status(400).json(err("LIKE_FAILED", result.get("error"))); return; }
            ctx.json(ok(result));
        });

        app.post("/api/stories/{storyId}/reaction", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            long storyId = ctx.pathParamAsClass("storyId", Long.class).get();
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            String reaction = (String) body.get("reaction");
            if (reaction == null) { ctx.status(400).json(err("INVALID_INPUT", "reaction required")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                var existing = listMaps(s, "SELECT id FROM story_reactions WHERE story_id = :sid AND user_id = :uid AND reaction = :r", "sid", storyId, "uid", user.getId(), "r", reaction);
                if (existing.isEmpty()) {
                    s.createNativeMutationQuery("INSERT INTO story_reactions (story_id, user_id, reaction, created_at) VALUES (:sid, :uid, :r, NOW())")
                            .setParameter("sid", storyId).setParameter("uid", user.getId()).setParameter("r", reaction).executeUpdate();
                }
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Reaction added")));
        });

        app.post("/api/stories/{storyId}/reply", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            long storyId = ctx.pathParamAsClass("storyId", Long.class).get();
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            String text = (String) body.get("text");
            if (text == null) { ctx.status(400).json(err("INVALID_INPUT", "text required")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                var rows = listMaps(s, "SELECT owner_id FROM stories WHERE id = :sid", "sid", storyId);
                if (rows.isEmpty()) { ctx.status(404).json(err("NOT_FOUND", "Story not found")); return; }
                long ownerId = ((Number) rows.get(0).get("owner_id")).longValue();
                s.beginTransaction();
                s.createNativeMutationQuery("INSERT INTO messages (sender_id, receiver_id, content, chat_id, created_at, is_read) VALUES (:uid, :oid, :text, (SELECT id FROM chats WHERE (user1_id = :uid AND user2_id = :oid) OR (user2_id = :uid AND user1_id = :oid) LIMIT 1), NOW(), false)")
                        .setParameter("uid", user.getId()).setParameter("oid", ownerId).setParameter("text", "Reply to story: " + text).executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Reply sent")));
        });

        app.get("/api/stories/{storyId}/stats", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            long storyId = ctx.pathParamAsClass("storyId", Long.class).get();
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                var views = listMaps(s, "SELECT COUNT(*) AS cnt FROM story_views WHERE story_id = :sid", "sid", storyId);
                var likes = listMaps(s, "SELECT COUNT(*) AS cnt FROM story_likes WHERE story_id = :sid", "sid", storyId);
                var reactions = listMaps(s, "SELECT reaction, COUNT(*) AS cnt FROM story_reactions WHERE story_id = :sid GROUP BY reaction", "sid", storyId);
                var viewers = listMaps(s, "SELECT u.id, u.username, u.display_name, u.avatar_url, sv.created_at AS viewed_at FROM story_views sv JOIN users u ON u.id = sv.user_id WHERE sv.story_id = :sid ORDER BY sv.created_at DESC", "sid", storyId);
                ctx.json(ok(Map.of("views", views.get(0).get("cnt"), "likes", likes.get(0).get("cnt"), "reactions", reactions, "viewers", viewers)));
            }
        });

        app.delete("/api/stories/{storyId}", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            long storyId = ctx.pathParamAsClass("storyId", Long.class).get();
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery("DELETE FROM story_reactions WHERE story_id = :sid").setParameter("sid", storyId).executeUpdate();
                s.createNativeMutationQuery("DELETE FROM story_likes WHERE story_id = :sid").setParameter("sid", storyId).executeUpdate();
                s.createNativeMutationQuery("DELETE FROM story_views WHERE story_id = :sid").setParameter("sid", storyId).executeUpdate();
                s.createNativeMutationQuery("DELETE FROM stories WHERE id = :sid AND owner_id = :uid")
                        .setParameter("sid", storyId).setParameter("uid", user.getId()).executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Story deleted")));
        });
    }
}
