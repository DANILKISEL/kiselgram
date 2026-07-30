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

public class RecentSearchRoutes {

    public static void registerRoutes(Javalin app, AuthService authService, MessageService messageService,
                                      ChatService chatService, StoryService storyService,
                                      AdminService adminService) {

        app.get("/api/recent_searches", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                ctx.json(ok(listMaps(s, "SELECT * FROM recent_searches WHERE user_id = :uid ORDER BY searched_at DESC LIMIT 20", "uid", user.getId())));
            }
        });

        app.post("/api/recent_searches", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            String query = (String) body.get("query");
            String type = (String) body.getOrDefault("type", "global");
            if (query == null) { ctx.status(400).json(err("INVALID_INPUT", "query required")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery("INSERT INTO recent_searches (user_id, query, search_type, searched_at) VALUES (:uid, :q, :type, NOW())")
                        .setParameter("uid", user.getId()).setParameter("q", query).setParameter("type", type).executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Search saved")));
        });

        app.delete("/api/recent_searches", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery("DELETE FROM recent_searches WHERE user_id = :uid")
                        .setParameter("uid", user.getId()).executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Recent searches cleared")));
        });
    }
}
