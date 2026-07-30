package ru.kiselgram.web.route;

import ru.kiselgram.web.model.CmsFile;
import ru.kiselgram.web.model.User;
import ru.kiselgram.web.service.AuthService;
import ru.kiselgram.web.service.FileService;
import ru.kiselgram.web.service.MessageService;
import ru.kiselgram.web.service.ChatService;
import ru.kiselgram.web.service.StoryService;
import ru.kiselgram.web.service.AdminService;
import io.javalin.Javalin;
import io.javalin.http.Context;
import io.javalin.http.UploadedFile;

import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

public class FileRoutes {

    private static FileService fileService;

    public static void registerRoutes(Javalin app, AuthService authService, MessageService messageService,
                                      ChatService chatService, StoryService storyService,
                                      AdminService adminService) {
        fileService = new FileService();

        app.post("/api/upload", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(error("UNAUTHORIZED", "Not authenticated")); return; }
            UploadedFile uploadedFile = ctx.uploadedFile("file");
            if (uploadedFile == null) { ctx.status(400).json(error("INVALID_INPUT", "File required")); return; }
            byte[] data;
            try (InputStream is = uploadedFile.content()) { data = is.readAllBytes(); }
            Map<String, Object> result = fileService.upload(user, data, uploadedFile.filename(), uploadedFile.contentType());
            if (result.containsKey("error")) { ctx.status(400).json(error("UPLOAD_FAILED", result.get("error"))); return; }
            ctx.json(success(result));
        });

        app.get("/api/files/{fileId}", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(error("UNAUTHORIZED", "Not authenticated")); return; }
            Long fileId = ctx.pathParamAsClass("fileId", Long.class).get();
            CmsFile file = fileService.getFile(fileId);
            if (file == null) { ctx.status(404).json(error("NOT_FOUND", "File not found")); return; }
            ctx.json(success(file.toMap()));
        });

        app.get("/api/files/{fileId}/download", ctx -> {
            CmsFile file = fileService.getFile(ctx.pathParamAsClass("fileId", Long.class).get());
            if (file == null) { ctx.status(404).json(error("NOT_FOUND", "File not found")); return; }
            Path p = fileService.getFilePath(file);
            if (!Files.exists(p)) { ctx.status(404).json(error("NOT_FOUND", "File not found on disk")); return; }
            ctx.contentType(file.getFileType() != null ? file.getFileType() : "application/octet-stream");
            ctx.header("Content-Disposition", "attachment; filename=\"" + file.getFileName() + "\"");
            ctx.result(Files.newInputStream(p));
        });

        app.delete("/api/files/{fileId}", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) { ctx.status(401).json(error("UNAUTHORIZED", "Not authenticated")); return; }
            Map<String, Object> result = fileService.deleteFile(user, ctx.pathParamAsClass("fileId", Long.class).get());
            if (result.containsKey("error")) { ctx.status(403).json(error("FORBIDDEN", result.get("error"))); return; }
            ctx.json(success(result));
        });
    }

    private static Map<String, Object> success(Object data) { return Map.of("success", true, "data", data); }
    private static Map<String, Object> error(String code, Object msg) { return Map.of("success", false, "error", Map.of("code", code, "message", msg)); }
}
