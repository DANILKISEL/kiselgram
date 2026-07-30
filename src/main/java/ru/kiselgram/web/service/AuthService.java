package ru.kiselgram.web.service;

import ru.kiselgram.web.config.AppConfig;
import ru.kiselgram.web.model.User;
import ru.kiselgram.web.model.LoginOtp;
import ru.kiselgram.web.model.EmailVerification;
import ru.kiselgram.web.repository.UserRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.nimbusds.jose.*;
import com.nimbusds.jose.crypto.MACSigner;
import com.nimbusds.jose.crypto.MACVerifier;
import com.nimbusds.jwt.JWTClaimsSet;
import com.nimbusds.jwt.SignedJWT;
import io.javalin.http.Context;
import org.hibernate.Session;

import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URI;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

import static ru.kiselgram.web.config.HibernateConfig.getInstance;

public class AuthService {

    private final UserRepository userRepository;

    public AuthService() {
        this.userRepository = new UserRepository();
    }

    public AuthService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    public Map<String, Object> register(String username, String email, String password) {
        try {
            if (userRepository.existsByUsername(username)) {
                return errorMap("Username already taken");
            }
            if (userRepository.existsByEmail(email)) {
                return errorMap("Email already registered");
            }

            User user = new User();
            user.setUsername(username);
            user.setEmail(email);
            user.setPassword(password);
            user.setEmailVerified(true);
            user = userRepository.save(user);

            try (Session s = getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                org.hibernate.query.Query<EmailVerification> q = s.createQuery(
                    "FROM EmailVerification WHERE email = :em AND userId IS NULL ORDER BY createdAt DESC",
                    EmailVerification.class);
                q.setParameter("em", email);
                q.setMaxResults(1);
                EmailVerification ev = q.uniqueResultOptional().orElse(null);
                if (ev == null) {
                    ev = new EmailVerification();
                    ev.setEmail(email);
                    ev.setVerificationCode(generateCode(6));
                    ev.setExpiresAt(LocalDateTime.now().plusHours(24));
                }
                ev.setUserId(user.getId());
                s.merge(ev);
                s.getTransaction().commit();
            } catch (Exception e) {
                e.printStackTrace();
            }

            String token = generateToken(user);
            Map<String, Object> result = new HashMap<>();
            result.put("session_token", token);
            result.put("user", userToClientMap(user));
            return result;
        } catch (Exception e) {
            return errorMap("Registration failed: " + e.getMessage());
        }
    }

    public Map<String, Object> login(String username, String password) {
        try {
            Optional<User> opt = userRepository.findByUsername(username);
            if (opt.isEmpty()) {
                return errorMap("Invalid username or password");
            }

            User user = opt.get();
            if (!user.checkPassword(password)) {
                return errorMap("Invalid username or password");
            }

            try (Session s = getInstance().getSessionFactory().openSession()) {
                s.beginTransaction();
                LoginOtp otp = new LoginOtp();
                otp.setUserId(user.getId());
                otp.setOtpCode(generateCode(6));
                otp.setPurpose("login");
                otp.setExpiresAt(LocalDateTime.now().plusMinutes(5));
                s.persist(otp);
                s.getTransaction().commit();
            } catch (Exception e) {
                e.printStackTrace();
            }

            String token = generateToken(user);
            Map<String, Object> result = new HashMap<>();
            result.put("session_token", token);
            result.put("user", userToClientMap(user));
            return result;
        } catch (Exception e) {
            return errorMap("Login failed: " + e.getMessage());
        }
    }

    private Map<String, Object> userToClientMap(User user) {
        Map<String, Object> m = new HashMap<>();
        m.put("user_id", user.getId());
        m.put("username", user.getUsername());
        m.put("display_name", user.getDisplayName());
        m.put("email", user.getEmail());
        m.put("email_verified", user.isEmailVerified());
        m.put("avatar_url", user.getAvatarUrl());
        m.put("bio", user.getBio());
        m.put("is_premium", false);
        return m;
    }

    public Map<String, Object> logout(Long userId) {
        Map<String, Object> result = new HashMap<>();
        result.put("success", true);
        return result;
    }

    public boolean verifyEmail(String token) {
        try {
            SignedJWT signedJWT = SignedJWT.parse(token);
            JWTClaimsSet claims = signedJWT.getJWTClaimsSet();
            Long userId = claims.getLongClaim("user_id");
            Optional<User> opt = userRepository.findById(userId);
            if (opt.isPresent()) {
                User user = opt.get();
                user.setEmailVerified(true);
                userRepository.update(user);
                return true;
            }
            return false;
        } catch (Exception e) {
            return false;
        }
    }

    public String generateToken(User user) {
        try {
            String secret = AppConfig.getInstance().getApp().getSecretKey();
            if (secret.length() < 32) {
                secret = padSecret(secret);
            }

            JWSSigner signer = new MACSigner(secret.getBytes());

            Instant now = Instant.now();
            JWTClaimsSet claimsSet = new JWTClaimsSet.Builder()
                    .subject(user.getId().toString())
                    .claim("user_id", user.getId())
                    .claim("username", user.getUsername())
                    .issueTime(Date.from(now))
                    .expirationTime(Date.from(now.plus(7, ChronoUnit.DAYS)))
                    .build();

            SignedJWT signedJWT = new SignedJWT(
                    new JWSHeader(JWSAlgorithm.HS256), claimsSet);
            signedJWT.sign(signer);
            return signedJWT.serialize();
        } catch (Exception e) {
            throw new RuntimeException("Failed to generate token", e);
        }
    }

    public JWTClaimsSet validateToken(String token) {
        try {
            String secret = AppConfig.getInstance().getApp().getSecretKey();
            if (secret.length() < 32) {
                secret = padSecret(secret);
            }

            SignedJWT signedJWT = SignedJWT.parse(token);
            JWSVerifier verifier = new MACVerifier(secret.getBytes());

            if (!signedJWT.verify(verifier)) {
                return null;
            }

            JWTClaimsSet claims = signedJWT.getJWTClaimsSet();
            if (claims.getExpirationTime().before(new Date())) {
                return null;
            }

            return claims;
        } catch (Exception e) {
            return null;
        }
    }

    public User getCurrentUser(Context ctx) {
        try {
            String authHeader = ctx.header("Authorization");
            if (authHeader != null && authHeader.startsWith("Bearer ")) {
                String token = authHeader.substring(7);
                JWTClaimsSet claims = validateToken(token);
                if (claims != null) {
                    Long userId = claims.getLongClaim("user_id");
                    return userRepository.findById(userId).orElse(null);
                }
            }

            String sessionId = ctx.cookie("session");
            if (sessionId != null) {
                JWTClaimsSet claims = validateToken(sessionId);
                if (claims != null) {
                    Long userId = claims.getLongClaim("user_id");
                    return userRepository.findById(userId).orElse(null);
                }
            }
        } catch (Exception e) {
            return null;
        }

        return null;
    }

    public Map<String, Object> googleOAuth(String code) {
        try {
            AppConfig.GoogleSection google = AppConfig.getInstance().getGoogle();
            ObjectMapper mapper = new ObjectMapper();

            String redirectUri = AppConfig.getInstance().getGoogle().getRedirectUri();
            String tokenResponse = httpPost("https://oauth2.googleapis.com/token",
                    "code=" + urlEncode(code) +
                    "&client_id=" + urlEncode(google.getClientId()) +
                    "&client_secret=" + urlEncode(google.getClientSecret()) +
                    "&redirect_uri=" + urlEncode(redirectUri) +
                    "&grant_type=authorization_code");

            JsonNode tokenJson = mapper.readTree(tokenResponse);
            JsonNode accessTokenNode = tokenJson.get("access_token");
            if (accessTokenNode == null) {
                String err = tokenJson.has("error") ? tokenJson.get("error").asText() : "unknown";
                return errorMap("Google token exchange failed: " + err);
            }

            String userInfoResponse = httpGet("https://www.googleapis.com/oauth2/v2/userinfo",
                    accessTokenNode.asText());
            JsonNode userInfo = mapper.readTree(userInfoResponse);

            String googleId = userInfo.get("id").asText();
            String email = userInfo.has("email") ? userInfo.get("email").asText() : null;
            String name = userInfo.has("name") ? userInfo.get("name").asText() : null;
            String picture = userInfo.has("picture") ? userInfo.get("picture").asText() : null;

            Optional<User> existing = userRepository.findByGoogleId(googleId);
            User user;
            if (existing.isPresent()) {
                user = existing.get();
            } else if (email != null) {
                existing = userRepository.findByEmail(email);
                if (existing.isPresent()) {
                    user = existing.get();
                    user.setGoogleId(googleId);
                    userRepository.update(user);
                } else {
                    user = createGoogleUser(googleId, email, name, picture);
                }
            } else {
                user = createGoogleUser(googleId, email, name, picture);
            }

            String token = generateToken(user);
            Map<String, Object> result = new HashMap<>();
            result.put("session_token", token);
            result.put("user", userToClientMap(user));
            return result;
        } catch (Exception e) {
            return errorMap("Google OAuth failed: " + e.getMessage());
        }
    }

    private User createGoogleUser(String googleId, String email, String name, String picture) {
        String baseUsername = (email != null) ? email.split("@")[0] : "user" + googleId.hashCode();
        String username = baseUsername;
        int suffix = 1;
        while (userRepository.existsByUsername(username)) {
            username = baseUsername + suffix;
            suffix++;
        }
        User user = new User();
        user.setUsername(username);
        user.setEmail(email);
        user.setGoogleId(googleId);
        user.setDisplayName(name != null ? name : username);
        user.setAvatarUrl(picture);
        user.setPassword(java.util.UUID.randomUUID().toString());
        user.setEmailVerified(email != null);
        return userRepository.save(user);
    }

    // Protected for testability — subclasses/spies can mock these
    protected String httpPost(String url, String body) throws Exception {
        HttpURLConnection conn = (HttpURLConnection) URI.create(url).toURL().openConnection();
        conn.setRequestMethod("POST");
        conn.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
        conn.setDoOutput(true);
        try (OutputStream os = conn.getOutputStream()) {
            os.write(body.getBytes(StandardCharsets.UTF_8));
        }
        return readResponse(conn);
    }

    protected String httpGet(String url, String accessToken) throws Exception {
        HttpURLConnection conn = (HttpURLConnection) URI.create(url).toURL().openConnection();
        conn.setRequestMethod("GET");
        conn.setRequestProperty("Authorization", "Bearer " + accessToken);
        return readResponse(conn);
    }

    private String readResponse(HttpURLConnection conn) throws Exception {
        int status = conn.getResponseCode();
        java.io.InputStream is = (status >= 200 && status < 300)
                ? conn.getInputStream()
                : conn.getErrorStream();
        return new String(is.readAllBytes(), StandardCharsets.UTF_8);
    }

    private String urlEncode(String value) {
        return URLEncoder.encode(value, StandardCharsets.UTF_8);
    }

    public Map<String, Object> loginByIdentifier(String identifier, String password) {
        try {
            Optional<User> opt = userRepository.findByUsername(identifier);
            if (opt.isEmpty()) {
                opt = userRepository.findByEmail(identifier);
            }
            if (opt.isEmpty()) {
                return errorMap("Invalid credentials");
            }
            User user = opt.get();
            if (password != null && !user.checkPassword(password)) {
                return errorMap("Invalid credentials");
            }
            String token = generateToken(user);
            Map<String, Object> result = new HashMap<>();
            result.put("session_token", token);
            result.put("user", userToClientMap(user));
            return result;
        } catch (Exception e) {
            return errorMap("Login failed: " + e.getMessage());
        }
    }

    public boolean checkUsername(String username) {
        return !userRepository.existsByUsername(username);
    }

    public boolean checkEmail(String email) {
        return userRepository.existsByEmail(email);
    }

    private Map<String, Object> errorMap(String message) {
        Map<String, Object> map = new HashMap<>();
        map.put("error", message);
        return map;
    }

    private String generateCode(int length) {
        SecureRandom random = new SecureRandom();
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < length; i++) {
            sb.append(random.nextInt(10));
        }
        return sb.toString();
    }

    private String padSecret(String secret) {
        StringBuilder sb = new StringBuilder(secret);
        while (sb.length() < 32) {
            sb.append("0");
        }
        return sb.toString();
    }
}
