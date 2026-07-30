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

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import static ru.kiselgram.web.route.RouteHelper.*;

public class PollRoutes {

    public static void registerRoutes(Javalin app, AuthService authService, MessageService messageService,
                                      ChatService chatService, StoryService storyService,
                                      AdminService adminService) {

        app.post("/api/polls/create", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            String question = (String) body.get("question");
            Object optionsRaw = body.get("options");
            Boolean anonymous = body.get("anonymous") != null && (Boolean) body.get("anonymous");
            if (question == null || optionsRaw == null) { ctx.status(400).json(err("INVALID_INPUT", "question and options required")); return; }
            List<String> options = ((List<String>) optionsRaw);
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery("INSERT INTO polls (question, created_by, is_anonymous, is_multiple_choice, created_at) VALUES (:q, :uid, :anon, false, NOW())")
                        .setParameter("q", question).setParameter("uid", user.getId())
                        .setParameter("anon", anonymous).executeUpdate();
                var pollRows = listMaps(s, "SELECT MAX(id) AS id FROM polls WHERE created_by = :uid", "uid", user.getId());
                long pollId = ((Number) pollRows.get(0).get("id")).longValue();
                for (String opt : options) {
                    s.createNativeMutationQuery("INSERT INTO poll_options (poll_id, option_text) VALUES (:pid, :text)")
                            .setParameter("pid", pollId).setParameter("text", opt).executeUpdate();
                }
                s.getTransaction().commit();
                ctx.json(ok(Map.of("poll_id", pollId, "message", "Poll created")));
            }
        });

        app.post("/api/polls/vote", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            Object pollId = body.get("poll_id");
            Object optionId = body.get("option_id");
            if (pollId == null || optionId == null) { ctx.status(400).json(err("INVALID_INPUT", "poll_id and option_id required")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                var existing = listMaps(s, "SELECT id FROM poll_votes WHERE poll_id = :pid AND user_id = :uid", "pid", ((Number) pollId).longValue(), "uid", user.getId());
                if (!existing.isEmpty()) {
                    s.createNativeMutationQuery("UPDATE poll_votes SET option_id = :oid WHERE poll_id = :pid AND user_id = :uid")
                            .setParameter("oid", ((Number) optionId).longValue()).setParameter("pid", ((Number) pollId).longValue()).setParameter("uid", user.getId()).executeUpdate();
                } else {
                    s.createNativeMutationQuery("INSERT INTO poll_votes (poll_id, option_id, user_id, voted_at) VALUES (:pid, :oid, :uid, NOW())")
                            .setParameter("pid", ((Number) pollId).longValue()).setParameter("oid", ((Number) optionId).longValue()).setParameter("uid", user.getId()).executeUpdate();
                }
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Vote recorded")));
        });

        app.get("/api/polls/{pollId}/results", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            long pollId = ctx.pathParamAsClass("pollId", Long.class).get();
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                var poll = listMaps(s, "SELECT * FROM polls WHERE id = :pid", "pid", pollId);
                if (poll.isEmpty()) { ctx.status(404).json(err("NOT_FOUND", "Poll not found")); return; }
                var options = listMaps(s, "SELECT option_text FROM poll_options WHERE poll_id = :pid", "pid", pollId);
                var votes = listMaps(s, "SELECT option_id, COUNT(*) AS cnt FROM poll_votes WHERE poll_id = :pid GROUP BY option_id", "pid", pollId);
                java.util.Map<Integer, Long> voteCount = new java.util.HashMap<>();
                for (var v : votes) {
                    voteCount.put(((Number) v.get("option_id")).intValue(), ((Number) v.get("cnt")).longValue());
                }
                java.util.List<java.util.Map<String, Object>> opts = new java.util.ArrayList<>();
                int idx = 0;
                for (var opt : options) {
                    java.util.Map<String, Object> o = new java.util.HashMap<>();
                    o.put("text", opt.get("option_text"));
                    o.put("index", idx);
                    o.put("votes", voteCount.getOrDefault(idx, 0L));
                    opts.add(o);
                    idx++;
                }
                ctx.json(ok(Map.of("poll", poll.get(0), "options", opts)));
            }
        });
    }
}
