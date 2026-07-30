package ru.kiselgram.web.route;

import ru.kiselgram.web.model.User;
import ru.kiselgram.web.service.AuthService;
import ru.kiselgram.web.service.MessageService;
import ru.kiselgram.web.service.ChatService;
import ru.kiselgram.web.service.StoryService;
import ru.kiselgram.web.service.AdminService;
import ru.kiselgram.web.service.DatabaseService;
import ru.kiselgram.web.service.FileService;
import org.hibernate.Session;
import io.javalin.Javalin;
import io.javalin.http.UploadedFile;

import java.io.InputStream;
import java.util.Map;

import static ru.kiselgram.web.route.RouteHelper.*;

public class MusicRoutes {

    private static FileService fileService = new FileService();

    public static void registerRoutes(Javalin app, AuthService authService, MessageService messageService,
                                      ChatService chatService, StoryService storyService,
                                      AdminService adminService) {

        app.get("/api/music", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                ctx.json(ok(listMaps(s,
                    "SELECT m.*, f.file_name, f.file_path, f.file_size FROM music_tracks m JOIN files f ON f.id = m.file_id ORDER BY m.created_at DESC")));
            }
        });

        app.get("/api/music/library", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                ctx.json(ok(listMaps(s,
                    "SELECT m.*, f.file_name, f.file_path, f.file_size FROM music_tracks m JOIN files f ON f.id = m.file_id ORDER BY m.created_at DESC")));
            }
        });

        app.post("/api/music", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            UploadedFile uploadedFile = ctx.uploadedFile("file");
            String title = ctx.formParam("title");
            String artist = ctx.formParam("artist");
            Integer duration = ctx.formParam("duration") != null ? Integer.parseInt(ctx.formParam("duration")) : null;
            if (uploadedFile == null) { ctx.status(400).json(err("INVALID_INPUT", "File required")); return; }
            byte[] data;
            try (InputStream is = uploadedFile.content()) { data = is.readAllBytes(); }
            Map<String, Object> uploaded = fileService.upload(user, data, uploadedFile.filename(), uploadedFile.contentType());
            if (uploaded.containsKey("error")) { ctx.status(400).json(err("UPLOAD_FAILED", uploaded.get("error"))); return; }
            Long fileId = ((Number) uploaded.get("id")).longValue();
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery(
                    "INSERT INTO music_tracks (file_id, title, artist, duration, uploader_id, created_at) VALUES (:fid, :title, :artist, :dur, :uid, NOW())")
                        .setParameter("fid", fileId).setParameter("title", title != null ? title : uploadedFile.filename())
                        .setParameter("artist", artist != null ? artist : "Unknown")
                        .setParameter("dur", duration).setParameter("uid", user.getId()).executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Track added", "file_id", fileId)));
        });

        app.delete("/api/music/{trackId}", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(err("UNAUTHORIZED", "Not authenticated")); return; }
            long trackId = ctx.pathParamAsClass("trackId", Long.class).get();
            try (Session s = DatabaseService.getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                s.createNativeMutationQuery("DELETE FROM music_tracks WHERE id = :id").setParameter("id", trackId).executeUpdate();
                s.getTransaction().commit();
            }
            ctx.json(ok(Map.of("message", "Track deleted")));
        });
    }
}
