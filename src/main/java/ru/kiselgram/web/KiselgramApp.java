package ru.kiselgram.web;

import ru.kiselgram.web.config.AppConfig;
import ru.kiselgram.web.config.HibernateConfig;
import ru.kiselgram.web.util.SecurityUtil;
import ru.kiselgram.web.service.AuthService;
import ru.kiselgram.web.service.MessageService;
import ru.kiselgram.web.service.ChatService;
import ru.kiselgram.web.service.StoryService;
import ru.kiselgram.web.service.AdminService;
import ru.kiselgram.web.model.User;
import ru.kiselgram.web.repository.UserRepository;

import ru.kiselgram.web.route.AuthRoutes;
import ru.kiselgram.web.route.MessageRoutes;
import ru.kiselgram.web.route.ChatRoutes;
import ru.kiselgram.web.route.GroupRoutes;
import ru.kiselgram.web.route.ChannelRoutes;
import ru.kiselgram.web.route.ContactRoutes;
import ru.kiselgram.web.route.ProfileRoutes;
import ru.kiselgram.web.route.SearchRoutes;
import ru.kiselgram.web.route.FileRoutes;
import ru.kiselgram.web.route.AdminRoutes;
import ru.kiselgram.web.route.StoryRoutes;
import ru.kiselgram.web.route.PremiumRoutes;
import ru.kiselgram.web.route.PushRoutes;
import ru.kiselgram.web.route.OAuthRoutes;
import ru.kiselgram.web.route.KSettingsRoutes;
import ru.kiselgram.web.route.QrLoginRoutes;
import ru.kiselgram.web.route.ReferralRoutes;
import ru.kiselgram.web.route.FeaturesRoutes;
import ru.kiselgram.web.route.SessionRoutes;
import ru.kiselgram.web.route.CallsRoutes;
import ru.kiselgram.web.route.SavedRoutes;
import ru.kiselgram.web.route.FavoriteRoutes;
import ru.kiselgram.web.route.MusicRoutes;
import ru.kiselgram.web.route.PinnedRoutes;
import ru.kiselgram.web.route.BotWebhookRoutes;
import ru.kiselgram.web.route.ForwardRoutes;
import ru.kiselgram.web.route.ReportRoutes;
import ru.kiselgram.web.route.BlockedRoutes;
import ru.kiselgram.web.route.MuteRoutes;
import ru.kiselgram.web.route.ArchiveRoutes;
import ru.kiselgram.web.route.OnlineRoutes;
import ru.kiselgram.web.route.PollRoutes;
import ru.kiselgram.web.route.InviteLinkRoutes;
import ru.kiselgram.web.route.MessagePinRoutes;
import ru.kiselgram.web.route.ReadReceiptRoutes;
import ru.kiselgram.web.route.GroupPermissionRoutes;
import ru.kiselgram.web.route.RecentSearchRoutes;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import io.javalin.Javalin;
import io.javalin.http.staticfiles.Location;
import io.javalin.json.JavalinJackson;
import java.util.Map;

public class KiselgramApp {
    public static void main(String[] args) {
        AppConfig config = AppConfig.getInstance();

        System.out.println("Starting Kiselgram Java v" + config.getApp().getVersion());

        HibernateConfig hibernateConfig = HibernateConfig.getInstance();

        AuthService authService = new AuthService();
        MessageService messageService = new MessageService();
        ChatService chatService = new ChatService();
        StoryService storyService = new StoryService();
        AdminService adminService = new AdminService();

        ObjectMapper objectMapper = new ObjectMapper()
                .registerModule(new JavaTimeModule());
        Javalin app = Javalin.create(javalinConfig -> {
            javalinConfig.staticFiles.add("/public");
            javalinConfig.staticFiles.add(c -> {
                c.hostedPath = "/static";
                c.directory = "/Users/dkisel/PycharmProjects/kiselgram-dev/static";
                c.location = Location.EXTERNAL;
            });
            javalinConfig.showJavalinBanner = false;
            javalinConfig.http.defaultContentType = "application/json";
            javalinConfig.jsonMapper(new JavalinJackson(objectMapper, false));
        });

        app.exception(Exception.class, (e, ctx) -> {
            System.err.println("ERROR in " + ctx.method() + " " + ctx.path() + ": " + e.getMessage());
            e.printStackTrace();
            Map<String, Object> err = new java.util.HashMap<>();
            err.put("success", false);
            err.put("error", Map.of("code", "INTERNAL_ERROR", "message", e.getMessage()));
            ctx.status(500).json(err);
        });

        app.before(ctx -> {
            ctx.header("Access-Control-Allow-Origin", "*");
            ctx.header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
            ctx.header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-CSRF-Token");
        });

        app.after(ctx -> {
            Map<String, String> headers = SecurityUtil.addSecurityHeaders();
            headers.forEach(ctx::header);
        });



        app.get("/health", ctx -> ctx.json(Map.of("status", "ok")));

        app.get("/", ctx -> {
            try {
                String html = java.nio.file.Files.readString(
                    java.nio.file.Path.of("/Users/dkisel/PycharmProjects/kiselgram-dev/templates/kiselgram-home.html"));
                html = html.replace("{{ url_for('auth.login') }}", "/auth/login")
                           .replace("{{ url_for('auth.register') }}", "/auth/register");
                ctx.contentType("text/html");
                ctx.result(html);
            } catch (Exception e) {
                ctx.redirect("/k#login");
            }
        });

        app.get("/k", ctx -> {
            var stream = KiselgramApp.class.getResourceAsStream("/public/k.html");
            if (stream != null) {
                ctx.contentType("text/html");
                ctx.result(new String(stream.readAllBytes()));
            } else {
                ctx.redirect("/k.html");
            }
        });

        app.get("/auth/login", ctx -> ctx.redirect("/k#login"));
        app.get("/auth/register", ctx -> ctx.redirect("/k#register"));

        app.get("/login.html", ctx -> {
            ctx.contentType("text/html");
            ctx.result("""
                <!DOCTYPE html>
                <html lang="en">
                <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width,initial-scale=1">
                <title>Kiselgram — Login</title>
                <style>
                *{margin:0;padding:0;box-sizing:border-box}
                body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0f0f1a;color:#f1f5f9;min-height:100vh;display:flex;align-items:center;justify-content:center}
                .card{background:#1e1b2e;border-radius:20px;padding:40px;width:380px;max-width:90vw;box-shadow:0 20px 60px rgba(0,0,0,.5)}
                h1{font-size:28px;font-weight:700;margin-bottom:4px;background:linear-gradient(135deg,#667eea,#764ba2);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
                .sub{color:#94a3b8;font-size:14px;margin-bottom:20px}
                input{width:100%;padding:12px 14px;border-radius:10px;border:1px solid #2d2a40;background:#0f0f1a;color:#f1f5f9;font-size:14px;outline:none;box-sizing:border-box;margin-bottom:12px}
                input:focus{border-color:#667eea}
                .btn{width:100%;padding:12px;border-radius:10px;border:none;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;font-size:15px;font-weight:600;cursor:pointer;margin-bottom:8px}
                .btn:hover{opacity:.9}
                .btn-sec{background:#2d2a40;color:#94a3b8;font-size:13px;margin-bottom:4px}
                .msg{padding:10px 14px;border-radius:10px;font-size:13px;display:none;margin-bottom:12px}
                .msg.err{display:block;background:#3d1a2e;color:#fca5a5;border:1px solid #7f1d1d}
                .msg.ok{display:block;background:#1a3d2e;color:#86efac;border:1px solid #166534}
                .dev{text-align:center;font-size:12px;color:#64748b;margin-top:16px;padding-top:16px;border-top:1px solid #2d2a40}
                .dev b{color:#94a3b8}
                .tabs{display:flex;gap:0;margin-bottom:20px;border-radius:10px;overflow:hidden;border:1px solid #2d2a40}
                .tab{flex:1;padding:10px 0;text-align:center;cursor:pointer;font-size:14px;font-weight:600;background:#2d2a40;color:#94a3b8;border:none}
                .tab.active{background:#667eea;color:#fff}
                </style>
                </head>
                <body>
                <div class="card">
                <h1>Kiselgram</h1>
                <div class="sub">Sign in or create an account</div>
                <div class="tabs">
                <button class="tab active" id="tabLogin" onclick="showLogin()">Login</button>
                <button class="tab" id="tabReg" onclick="showReg()">Register</button>
                </div>
                <div id="msg" class="msg"></div>
                <input id="userInput" type="text" placeholder="Username" autocomplete="username">
                <input id="emailInput" type="email" placeholder="Email (for registration)" autocomplete="email" style="display:none">
                <input id="passInput" type="password" placeholder="Password" autocomplete="current-password">
                <button class="btn" id="submitBtn" onclick="doLogin()">Sign In</button>
                </div>
                <script>
                function msg(text,type){var m=document.getElementById('msg');m.className='msg '+(type||'err');m.textContent=text||''}
                function showLogin(){document.getElementById('tabLogin').className='tab active';document.getElementById('tabReg').className='tab';document.getElementById('emailInput').style.display='none';document.getElementById('submitBtn').textContent='Sign In';document.getElementById('submitBtn').onclick=doLogin;msg('')}
                function showReg(){document.getElementById('tabLogin').className='tab';document.getElementById('tabReg').className='tab active';document.getElementById('emailInput').style.display='block';document.getElementById('submitBtn').textContent='Create Account';document.getElementById('submitBtn').onclick=doRegister;msg('')}
                async function doLogin(){var u=document.getElementById('userInput').value.trim(),p=document.getElementById('passInput').value;if(!u||!p){msg('Fill in both fields');return}
                try{var r=await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,password:p})});var j=await r.json()
                if(j.success){var a=[{username:j.data.user.username,displayName:j.data.user.display_name||j.data.user.username,avatarUrl:j.data.user.avatar_url||'',userId:j.data.user.user_id,token:j.data.session_token}];localStorage.setItem('k_accounts',JSON.stringify(a));window.location.href='/k.html'}
                else{msg((j.error&&j.error.message)||'Login failed')}}catch(e){msg('Error: '+e.message)}}
                async function doRegister(){var u=document.getElementById('userInput').value.trim(),e=document.getElementById('emailInput').value.trim(),p=document.getElementById('passInput').value;if(!u||!e||!p){msg('Fill in all fields');return}
                try{var r=await fetch('/api/auth/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u,email:e,password:p})});var j=await r.json()
                if(j.success){var a=[{username:j.data.user.username,displayName:j.data.user.display_name||j.data.user.username,avatarUrl:j.data.user.avatar_url||'',userId:j.data.user.user_id,token:j.data.session_token}];localStorage.setItem('k_accounts',JSON.stringify(a));window.location.href='/k.html'}
                else{msg((j.error&&j.error.message)||'Registration failed')}}catch(e){msg('Error: '+e.message)}}
                document.getElementById('passInput').addEventListener('keydown',function(e){if(e.key==='Enter'){if(document.getElementById('submitBtn').textContent==='Sign In')doLogin();else doRegister()}});
                </script>
                </body>
                </html>
                """);
        });

        AuthRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        MessageRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        ChatRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        GroupRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        ChannelRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        ContactRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        ProfileRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        SearchRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        FileRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        AdminRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        StoryRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        PremiumRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        PushRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        OAuthRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        KSettingsRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        QrLoginRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        ReferralRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        FeaturesRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        SessionRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        CallsRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        SavedRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        FavoriteRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        MusicRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        PinnedRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        BotWebhookRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        ForwardRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        ReportRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        BlockedRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        MuteRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        ArchiveRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        OnlineRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        PollRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        InviteLinkRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        MessagePinRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        ReadReceiptRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        GroupPermissionRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);
        RecentSearchRoutes.registerRoutes(app, authService, messageService, chatService, storyService, adminService);

        // Dev bootstrap: create test user if no users exist
        try {
            UserRepository userRepo = new UserRepository();
            if (userRepo.findAllActive().isEmpty()) {
                User dev = new User();
                dev.setUsername("dev");
                dev.setDisplayName("Developer");
                dev.setEmail("dev@kiselgram.ru");
                dev.setPassword("dev123");
                dev.setEmailVerified(true);
                dev.setAdmin(true);
                dev.setBio("Dev account for testing");
                userRepo.save(dev);
                System.out.println("Dev user created: username=dev password=dev123");
            }
        } catch (Exception e) {
            System.out.println("Skipping dev bootstrap: " + e.getMessage());
        }

        Thread storyCleanup = new Thread(() -> {
            while (true) {
                try {
                    Thread.sleep(1800_000);
                    storyService.deleteExpiredStories();
                } catch (InterruptedException e) {
                    break;
                } catch (Exception e) {
                    System.err.println("Story cleanup error: " + e.getMessage());
                }
            }
        });
        storyCleanup.setDaemon(true);
        storyCleanup.start();

        // Auth-only server for auth.kiselgram.ru
        Javalin authApp = Javalin.create(cfg -> {
            cfg.showJavalinBanner = false;
            cfg.http.defaultContentType = "application/json";
            cfg.jsonMapper(new JavalinJackson(objectMapper, false));
        });
        authApp.before(ctx -> {
            ctx.header("Access-Control-Allow-Origin", "*");
            ctx.header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
            ctx.header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-CSRF-Token");
        });
        authApp.get("/health", ctx -> ctx.json(Map.of("status", "ok")));
        AuthRoutes.registerRoutes(authApp, authService, messageService, chatService, storyService, adminService, "");
        OAuthRoutes.registerRoutes(authApp, authService, messageService, chatService, storyService, adminService, "");
        SessionRoutes.registerRoutes(authApp, authService, messageService, chatService, storyService, adminService, "");
        int authPort = config.getAuth().getPort();
        authApp.start(authPort);
        System.out.println("Auth server started on http://0.0.0.0:" + authPort + " (auth.kiselgram.ru)");

        // k.kiselgram.ru
        app.get("/.k", ctx -> ctx.json(Map.of("service", "k", "status", "ok")));
        app.get("/k-app", ctx -> {
            var stream = KiselgramApp.class.getResourceAsStream("/public/k.html");
            if (stream != null) {
                ctx.contentType("text/html");
                ctx.result(new String(stream.readAllBytes()));
            } else {
                ctx.redirect("/k");
            }
        });

        int port = config.getApp().getPort();
        app.start(port);
        System.out.println("Kiselgram started on http://0.0.0.0:" + port + " (web.kiselgram.ru, k.kiselgram.ru)");
    }
}
