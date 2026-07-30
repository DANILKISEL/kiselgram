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

import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;

public class AdminRoutes {

    private static AdminService adminService;
    private static AuthService authService;

    public static void registerRoutes(Javalin app, AuthService as, MessageService messageService,
                                      ChatService chatService, StoryService storyService,
                                      AdminService ad) {
        authService = as;
        adminService = ad;

        app.post("/api/admin/login", ctx -> {
            String username = ctx.formParam("username");
            String password = ctx.formParam("password");
            User user = null;
            if (username != null && password != null) {
                var opt = new ru.kiselgram.web.repository.UserRepository().findByUsername(username);
                if (opt.isPresent() && opt.get().isAdmin() && opt.get().checkPassword(password))
                    user = opt.get();
            }
            if (user != null) {
                String token = authService.generateToken(user);
                ctx.cookie("session", token, 604800);
                ctx.redirect("/api/admin");
            } else {
                String html = loadAdminHtml(ctx);
                if (html == null) return;
                html = html.replace("class=\"login-container\"", "class=\"login-container\"")
                    .replace("<div id=\"loginError\" class=\"login-error hidden\"></div>",
                        "<div id=\"loginError\" class=\"login-error\">Invalid credentials</div>");
                ctx.contentType("text/html");
                ctx.result(html);
            }
        });

        app.get("/api/admin/logout", ctx -> {
            ctx.removeCookie("session");
            ctx.redirect("/api/admin");
        });

        app.get("/api/admin", ctx -> {
            User user = authService.getCurrentUser(ctx);
            boolean isAdmin = user != null && user.isAdmin();
            String html = loadAdminHtml(ctx);
            if (html == null) return;
            if (isAdmin) {
                html = html.replace("id=\"userInfo\"></div>",
                    "id=\"userInfo\"><i class=\"fas fa-user\"></i> " + user.getUsername() + " <a href=\"/api/admin/logout\" class=\"btn btn-sm\">Logout</a>");
                html = html.replace("id=\"loginView\"", "id=\"loginView\" style=\"display:none\"");
                html = html.replace("id=\"adminView\" class=\"hidden\"", "id=\"adminView\"");
            }
            ctx.contentType("text/html");
            ctx.result(html);
        });

        app.get("/api/admin/stats", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null || !user.isAdmin()) {
                ctx.status(403).json(Map.of("success", false, "error",
                        Map.of("code", "FORBIDDEN", "message", "Admin access required")));
                return;
            }
            Map<String, Object> stats = adminService.getDashboardStats();
            ctx.json(Map.of("success", true, "data", stats));
        });

        app.get("/api/admin/users", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null || !user.isAdmin()) {
                ctx.status(403).json(Map.of("success", false, "error",
                        Map.of("code", "FORBIDDEN", "message", "Admin access required")));
                return;
            }
            int page = parseIntParam(ctx.queryParam("page"), 1);
            int perPage = Math.min(parseIntParam(ctx.queryParam("per_page"), 50), 100);
            List<Map<String, Object>> users = adminService.getUsers(page, perPage);
            ctx.json(Map.of("success", true, "data", Map.of("users", users)));
        });

        app.post("/api/admin/users/create", ctx -> {
            if (!isAdminUser(ctx)) return;
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            String username = (String) body.get("username");
            String email = (String) body.get("email");
            String password = (String) body.get("password");
            Map<String, Object> result = adminService.createUser(username, email, password);
            if (result.containsKey("error")) {
                ctx.status(400).json(Map.of("success", false, "error",
                    Map.of("code", "CREATE_FAILED", "message", result.get("error"))));
                return;
            }
            ctx.json(Map.of("success", true, "data", result));
        });

        app.post("/api/admin/users/{userId}/update", ctx -> {
            if (!isAdminUser(ctx)) return;
            Long userId = ctx.pathParamAsClass("userId", Long.class).get();
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            String username = (String) body.get("username");
            String email = (String) body.get("email");
            Map<String, Object> result = adminService.updateUser(userId, username, email);
            if (result.containsKey("error")) {
                ctx.status(400).json(Map.of("success", false, "error",
                    Map.of("code", "UPDATE_FAILED", "message", result.get("error"))));
                return;
            }
            ctx.json(Map.of("success", true, "data", result));
        });

        app.post("/api/admin/users/{userId}/set-password", ctx -> {
            if (!isAdminUser(ctx)) return;
            Long userId = ctx.pathParamAsClass("userId", Long.class).get();
            Map<String, Object> body = ctx.bodyAsClass(Map.class);
            String password = (String) body.get("password");
            Map<String, Object> result = adminService.setUserPassword(userId, password);
            if (result.containsKey("error")) {
                ctx.status(400).json(Map.of("success", false, "error",
                    Map.of("code", "PASSWORD_FAILED", "message", result.get("error"))));
                return;
            }
            ctx.json(Map.of("success", true, "data", result));
        });

        app.post("/api/admin/users/{userId}/toggle-admin", ctx -> {
            if (!isAdminUser(ctx)) return;
            User admin = authService.getCurrentUser(ctx);
            Long userId = ctx.pathParamAsClass("userId", Long.class).get();
            Map<String, Object> result = adminService.toggleAdmin(admin.getId(), userId);
            if (result.containsKey("error")) {
                ctx.status(400).json(Map.of("success", false, "error",
                    Map.of("code", "TOGGLE_FAILED", "message", result.get("error"))));
                return;
            }
            ctx.json(Map.of("success", true, "data", result));
        });

        app.post("/api/admin/users/{userId}/delete", ctx -> {
            if (!isAdminUser(ctx)) return;
            User admin = authService.getCurrentUser(ctx);
            Long userId = ctx.pathParamAsClass("userId", Long.class).get();
            Map<String, Object> result = adminService.deleteUserByAdmin(admin.getId(), userId);
            if (result.containsKey("error")) {
                ctx.status(400).json(Map.of("success", false, "error",
                    Map.of("code", "DELETE_FAILED", "message", result.get("error"))));
                return;
            }
            ctx.json(Map.of("success", true, "data", result));
        });

        app.delete("/api/admin/users/{userId}", ctx -> {
            User admin = authService.getCurrentUser(ctx);
            if (admin == null || !admin.isAdmin()) {
                ctx.status(403).json(Map.of("success", false, "error",
                        Map.of("code", "FORBIDDEN", "message", "Admin access required")));
                return;
            }
            Long userId = ctx.pathParamAsClass("userId", Long.class).get();
            Map<String, Object> result = adminService.deleteUserByAdmin(admin.getId(), userId);
            if (result.containsKey("error")) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "DELETE_FAILED", "message", result.get("error"))));
                return;
            }
            ctx.json(Map.of("success", true, "data", result));
        });

        app.get("/api/admin/reports", ctx -> {
            User user = authService.getCurrentUser(ctx);
            if (user == null || !user.isAdmin()) {
                ctx.status(403).json(Map.of("success", false, "error",
                        Map.of("code", "FORBIDDEN", "message", "Admin access required")));
                return;
            }
            int page = parseIntParam(ctx.queryParam("page"), 1);
            int perPage = Math.min(parseIntParam(ctx.queryParam("per_page"), 50), 100);
            List<Map<String, Object>> reports = adminService.getReports(page, perPage);
            ctx.json(Map.of("success", true, "data", Map.of("reports", reports)));
        });

        app.post("/api/admin/reports/{reportId}/resolve", ctx -> {
            User admin = authService.getCurrentUser(ctx);
            if (admin == null || !admin.isAdmin()) {
                ctx.status(403).json(Map.of("success", false, "error",
                        Map.of("code", "FORBIDDEN", "message", "Admin access required")));
                return;
            }
            Long reportId = ctx.pathParamAsClass("reportId", Long.class).get();
            Map<String, Object> result = adminService.resolveReport(reportId, admin.getId());
            if (result.containsKey("error")) {
                ctx.status(400).json(Map.of("success", false, "error",
                        Map.of("code", "RESOLVE_FAILED", "message", result.get("error"))));
                return;
            }
            ctx.json(Map.of("success", true, "data", result));
        });

        app.get("/api/admin/dashboard", ctx -> {
            if (!isAdminUser(ctx)) return;
            Map<String, Object> stats = adminService.getDashboardStats();
            ctx.json(Map.of("success", true, "data", stats));
        });

        app.get("/api/admin/2fa/overview", ctx -> {
            if (!isAdminUser(ctx)) return;
            ctx.json(Map.of("success", true, "data", adminService.getTwofaOverview()));
        });

        app.get("/api/admin/2fa/email-codes", ctx -> {
            if (!isAdminUser(ctx)) return;
            int perPage = Math.min(parseIntParam(ctx.queryParam("per_page"), 50), 100);
            ctx.json(Map.of("success", true, "data", adminService.getEmailVerifications(perPage)));
        });

        app.get("/api/admin/2fa/otps", ctx -> {
            if (!isAdminUser(ctx)) return;
            int perPage = Math.min(parseIntParam(ctx.queryParam("per_page"), 50), 100);
            ctx.json(Map.of("success", true, "data", adminService.getOtps(perPage)));
        });

        app.post("/api/admin/2fa/cleanup", ctx -> {
            if (!isAdminUser(ctx)) return;
            Map<String, Object> result = adminService.cleanupOtps();
            if (result.containsKey("error")) {
                ctx.status(400).json(Map.of("success", false, "error",
                    Map.of("code", "CLEANUP_FAILED", "message", result.get("error"))));
                return;
            }
            ctx.json(Map.of("success", true, "data", result.get("data")));
        });

        app.post("/api/admin/2fa/email-codes/cleanup", ctx -> {
            if (!isAdminUser(ctx)) return;
            Map<String, Object> result = adminService.cleanupEmailVerifications();
            if (result.containsKey("error")) {
                ctx.status(400).json(Map.of("success", false, "error",
                    Map.of("code", "CLEANUP_FAILED", "message", result.get("error"))));
                return;
            }
            ctx.json(Map.of("success", true, "data", result.get("data")));
        });

        app.post("/api/admin/terminal/exec", ctx -> {
            if (!isAdminUser(ctx)) return;
            ctx.json(Map.of("success", true, "data", Map.of("stdout", "Terminal disabled on Java backend", "stderr", "", "return_code", 0)));
        });

        app.get("/api/admin/promo/list", ctx -> {
            if (!isAdminUser(ctx)) return;
            ctx.json(Map.of("success", true, "promo_codes", List.of()));
        });

        app.get("/api/admin/mail/accounts", ctx -> {
            if (!isAdminUser(ctx)) return;
            ctx.json(Map.of("success", true, "data", List.of()));
        });

        app.get("/api/admin/chats", ctx -> {
            if (!isAdminUser(ctx)) return;
            ctx.json(Map.of("success", true, "data", Map.of("chats", List.of(), "page", 1, "per_page", 50, "total", 0, "total_pages", 1)));
        });
    }

    private static boolean isAdminUser(Context ctx) {
        User user = authService.getCurrentUser(ctx);
        if (user == null || !user.isAdmin()) {
            ctx.status(403).json(Map.of("success", false, "error",
                    Map.of("code", "FORBIDDEN", "message", "Admin access required")));
            return false;
        }
        return true;
    }

    private static String loadAdminHtml(Context ctx) {
        try {
            InputStream is = AdminRoutes.class.getClassLoader().getResourceAsStream("public/admin.html");
            if (is == null) {
                ctx.status(500).json(Map.of("success", false, "error",
                    Map.of("code", "ERROR", "message", "Admin template not found")));
                return null;
            }
            return new String(is.readAllBytes(), StandardCharsets.UTF_8);
        } catch (Exception e) {
            ctx.status(500).json(Map.of("success", false, "error",
                Map.of("code", "ERROR", "message", "Failed to load admin page")));
            return null;
        }
    }

    private static int parseIntParam(String val, int def) {
        if (val == null) return def;
        try { return Integer.parseInt(val); } catch (NumberFormatException e) { return def; }
    }
}
