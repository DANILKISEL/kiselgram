package ru.kiselgram.web.route;

import ru.kiselgram.web.config.AppConfig;
import ru.kiselgram.web.model.User;
import ru.kiselgram.web.service.AuthService;
import ru.kiselgram.web.service.MessageService;
import ru.kiselgram.web.service.ChatService;
import ru.kiselgram.web.service.StoryService;
import ru.kiselgram.web.service.AdminService;
import io.javalin.Javalin;
import io.javalin.http.Context;

import java.util.HashMap;
import java.util.Map;

public class FeaturesRoutes {

    public static void registerRoutes(Javalin app, AuthService authService, MessageService messageService,
                                      ChatService chatService, StoryService storyService,
                                      AdminService adminService) {

        app.get("/api/features", ctx -> {
            AppConfig.FeaturesSection features = AppConfig.getInstance().getFeatures();
            Map<String, Object> data = new HashMap<>();
            data.put("groups", features.isGroups());
            data.put("channels", features.isChannels());
            data.put("bots", features.isBots());
            data.put("video_streaming", features.isVideoStreaming());
            data.put("file_sharing", features.isFileSharing());
            data.put("reactions", features.isReactions());
            data.put("stories", true);
            data.put("music", true);
            data.put("calls", true);
            data.put("saved_messages", true);
            data.put("pinned_chats", true);
            data.put("favorites", true);
            data.put("forwarding", true);
            data.put("reporting", true);
            data.put("blocking", true);
            data.put("muting", true);
            data.put("archiving", true);
            data.put("online_status", true);
            data.put("search", true);
            data.put("file_uploads", true);
            data.put("voice_messages", true);
            data.put("two_factor_auth", features.isTwoFactorAuth());
            data.put("premium", features.isPremium());
            ctx.json(Map.of("success", true, "data", data));
        });
    }
}
