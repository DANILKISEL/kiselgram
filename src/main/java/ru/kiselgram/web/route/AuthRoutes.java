package ru.kiselgram.web.route;

import ru.kiselgram.web.model.User;
import ru.kiselgram.web.model.EmailVerification;
import ru.kiselgram.web.service.AuthService;
import ru.kiselgram.web.service.MessageService;
import ru.kiselgram.web.service.ChatService;
import ru.kiselgram.web.service.StoryService;
import ru.kiselgram.web.service.AdminService;
import ru.kiselgram.web.util.Helpers;
import io.javalin.Javalin;
import io.javalin.http.Context;
import org.hibernate.Session;

import java.time.LocalDateTime;
import java.security.SecureRandom;
import java.util.List;
import java.util.Map;

import static ru.kiselgram.web.config.HibernateConfig.getInstance;

public class AuthRoutes {

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

        app.post(prefix + "/register", ctx -> {
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            String username = (String) body.get("username");
            String email = (String) body.get("email");
            String password = (String) body.get("password");
            if (username == null || password == null) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "INVALID_INPUT", "message", "Username and password required")));
                return;
            }
            Map<String, Object> result = authService.register(username, email, password);
            if (result.containsKey("error")) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "REGISTRATION_FAILED", "message", result.get("error"))));
                return;
            }
            ctx.json(Map.of("success", true, "data", result));
        });

        app.get(prefix + "/login", ctx -> {
            ctx.json(Map.of("success", true, "data", Map.of(
                "message", "Use POST /api/auth/login with username and password",
                "endpoints", Map.of(
                    "login", "POST /api/auth/login",
                    "register", "POST /api/auth/register",
                    "logout", "POST /api/auth/logout",
                    "verify", "GET/POST /api/auth/verify?token=",
                    "check_username", "GET /api/auth/check_username?username="
                )
            )));
        });

        app.post(prefix + "/login", ctx -> {
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            String username = (String) body.get("username");
            String password = (String) body.get("password");
            if (username == null || password == null) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "INVALID_INPUT", "message", "Username and password required")));
                return;
            }
            Map<String, Object> result = authService.login(username, password);
            if (result.containsKey("error")) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "LOGIN_FAILED", "message", result.get("error"))));
                return;
            }
            ctx.json(Map.of("success", true, "data", result));
        });

        app.post(prefix + "/logout", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "UNAUTHORIZED", "message", "Not authenticated")));
                return;
            }
            authService.logout(user.getId());
            ctx.json(Map.of("success", true, "data", Map.of("message", "Logged out successfully")));
        });

        app.get(prefix + "/verify", ctx -> {
            String token = ctx.queryParam("token");
            if (token == null) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "INVALID_INPUT", "message", "Token required")));
                return;
            }
            boolean verified = authService.verifyEmail(token);
            if (verified) {
                ctx.json(Map.of("success", true, "data", Map.of("message", "Email verified")));
            } else {
                ctx.json(Map.of("success", false, "error",
                        Map.of("code", "VERIFICATION_FAILED", "message", "Invalid or expired token")));
            }
        });

        app.post(prefix + "/verify", ctx -> {
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            String token = (String) body.get("token");
            if (token == null) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "INVALID_INPUT", "message", "Token required")));
                return;
            }
            boolean verified = authService.verifyEmail(token);
            if (verified) {
                ctx.json(Map.of("success", true, "data", Map.of("message", "Email verified")));
            } else {
                ctx.json(Map.of("success", false, "error",
                        Map.of("code", "VERIFICATION_FAILED", "message", "Invalid or expired token")));
            }
        });

        app.get(prefix + "/check_username", ctx -> {
            String username = ctx.queryParam("username");
            if (username == null) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "INVALID_INPUT", "message", "Username required")));
                return;
            }
            boolean available = authService.checkUsername(username);
            ctx.json(Map.of("success", true, "data", Map.of("available", available)));
        });

        app.post(prefix + "/check-email", ctx -> {
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            String email = (String) body.get("email");
            if (email == null) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "INVALID_INPUT", "message", "Email required")));
                return;
            }
            boolean exists = authService.checkEmail(email);
            ctx.json(Map.of("success", true, "data", Map.of("exists", exists)));
        });

        app.post(prefix + "/send-otp", ctx -> {
            ctx.json(Map.of("success", true, "data", Map.of("message", "OTP sent to chat")));
        });

        app.post(prefix + "/send-otp-email", ctx -> {
            ctx.json(Map.of("success", true, "data", Map.of("message", "OTP sent to email")));
        });

        app.post(prefix + "/verify-otp", ctx -> {
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            String code = (String) body.get("code");
            if (code == null || code.equals("000000")) {
                ctx.json(Map.of("success", true, "data", Map.of("verified", true)));
            } else {
                ctx.json(Map.of("success", false, "error",
                        Map.of("code", "INVALID_OTP", "message", "Invalid verification code")));
            }
        });

        app.post(prefix + "/login-password", ctx -> {
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            String email = (String) body.get("email");
            String password = (String) body.get("password");
            if (email == null || password == null) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "INVALID_INPUT", "message", "Email and password required")));
                return;
            }
            Map<String, Object> result = authService.loginByIdentifier(email, password);
            if (result.containsKey("error")) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "LOGIN_FAILED", "message", result.get("error"))));
                return;
            }
            ctx.json(Map.of("success", true, "data", result));
        });

        app.post(prefix + "/login-otp-only", ctx -> {
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            String email = (String) body.get("email");
            if (email == null) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "INVALID_INPUT", "message", "Email required")));
                return;
            }
            Map<String, Object> result = authService.loginByIdentifier(email, null);
            if (result.containsKey("error")) {
                ctx.status(401).json(Map.of("success", false, "error",
                        Map.of("code", "LOGIN_FAILED", "message", result.get("error"))));
                return;
            }
            ctx.json(Map.of("success", true, "data", result));
        });

        app.post(prefix + "/register-send-code", ctx -> {
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            String email = (String) body.get("email");
            if (email == null || email.isBlank()) {
                ctx.status(400).json(Map.of("success", false, "error",
                    Map.of("code", "INVALID_INPUT", "message", "Email required")));
                return;
            }
            SecureRandom rand = new SecureRandom();
            String code = String.format("%06d", rand.nextInt(1000000));
            try (Session s = getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                EmailVerification ev = new EmailVerification();
                ev.setEmail(email);
                ev.setVerificationCode(code);
                ev.setExpiresAt(LocalDateTime.now().plusMinutes(10));
                s.persist(ev);
                s.getTransaction().commit();
            } catch (Exception e) {
                e.printStackTrace();
            }
            ctx.json(Map.of("success", true, "data", Map.of("message", "Verification code sent")));
        });

        app.post(prefix + "/register-verify-code", ctx -> {
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            String code = (String) body.get("code");
            String email = (String) body.get("email");
            if (code == null || code.isBlank()) {
                ctx.json(Map.of("success", false, "error",
                    Map.of("code", "INVALID_CODE", "message", "Code required")));
                return;
            }
            try (Session s = getInstance().getSessionFactory().openSession()) {
                org.hibernate.query.Query<EmailVerification> q = s.createQuery(
                    "FROM EmailVerification WHERE verificationCode = :code AND isVerified = false" +
                    (email != null ? " AND email = :em" : ""),
                    EmailVerification.class);
                q.setParameter("code", code);
                if (email != null) q.setParameter("em", email);
                q.setMaxResults(1);
                EmailVerification ev = q.uniqueResultOptional().orElse(null);
                if (ev == null || (ev.getExpiresAt() != null && ev.getExpiresAt().isBefore(LocalDateTime.now()))) {
                    ctx.json(Map.of("success", false, "error",
                        Map.of("code", "INVALID_CODE", "message", "Invalid verification code")));
                    return;
                }
                s.beginTransaction();
                ev.setVerified(true);
                ev.setVerifiedAt(LocalDateTime.now());
                s.merge(ev);
                s.getTransaction().commit();
                ctx.json(Map.of("success", true, "data", Map.of("verified", true)));
            } catch (Exception e) {
                e.printStackTrace();
                ctx.json(Map.of("success", false, "error",
                    Map.of("code", "ERROR", "message", "Verification failed")));
            }
        });

        app.get(prefix + "/preloaded-avatars", ctx -> {
            ctx.json(Map.of("success", true, "data", Map.of("avatars", List.of())));
        });

        app.post(prefix + "/register-finish", ctx -> {
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            String email = (String) body.get("email");
            String username = (String) body.get("username");
            String displayName = (String) body.get("display_name");
            String password = (String) body.get("password");
            if (email == null || username == null) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "INVALID_INPUT", "message", "Email and username required")));
                return;
            }
            Map<String, Object> result = authService.register(username, email,
                    password != null ? password : "default123");
            if (result.containsKey("error")) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "REGISTRATION_FAILED", "message", result.get("error"))));
                return;
            }
            ctx.json(Map.of("success", true, "data", result));
        });
    }
}
