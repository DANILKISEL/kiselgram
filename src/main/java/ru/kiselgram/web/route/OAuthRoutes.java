package ru.kiselgram.web.route;

import ru.kiselgram.web.config.AppConfig;
import ru.kiselgram.web.model.User;
import ru.kiselgram.web.service.AuthService;
import ru.kiselgram.web.service.MessageService;
import ru.kiselgram.web.service.ChatService;
import ru.kiselgram.web.service.StoryService;
import ru.kiselgram.web.service.AdminService;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.javalin.Javalin;
import io.javalin.http.Context;

import java.util.Map;

public class OAuthRoutes {

    private static AuthService authService;

    public static void registerRoutes(Javalin app, AuthService as, MessageService messageService,
                                      ChatService chatService, StoryService storyService,
                                      AdminService adminService) {
        registerRoutes(app, as, messageService, chatService, storyService, adminService, "/api/auth");
    }

    public static void registerRoutes(Javalin app, AuthService as, MessageService messageService,
                                      ChatService chatService, StoryService storyService,
                                      AdminService adminService, String prefix) {
        authService = as;
        AppConfig config = AppConfig.getInstance();

        app.get(prefix + "/oauth/google/login", ctx -> {
            String clientId = config.getGoogle().getClientId();
            String redirectUri = config.getGoogle().getRedirectUri();
            String googleUrl = "https://accounts.google.com/o/oauth2/v2/auth?"
                    + "client_id=" + clientId
                    + "&redirect_uri=" + redirectUri
                    + "&response_type=code"
                    + "&scope=openid%20email%20profile";
            ctx.redirect(googleUrl);
        });

        app.get(prefix + "/oauth/google/callback", ctx -> {
            String code = ctx.queryParam("code");
            String errorParam = ctx.queryParam("error");
            if (errorParam != null) {
                ctx.contentType("text/html");
                ctx.result("<html><body><script>window.opener.postMessage(" +
                        "{\"success\":false,\"error\":{\"message\":\"" + errorParam + "\"}},'*');window.close();</script></body></html>");
                return;
            }
            if (code == null) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "INVALID_INPUT", "message", "Authorization code required")));
                return;
            }
            Map<String, Object> result = authService.googleOAuth(code);
            ObjectMapper mapper = new ObjectMapper();
            String json = mapper.writeValueAsString(Map.of("success", true, "data", result));
            ctx.contentType("text/html");
            ctx.result("<html><body><script>" +
                    "window.opener.postMessage(" + json + ",'*');window.close();" +
                    "</script></body></html>");
        });
    }
}
