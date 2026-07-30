package ru.kiselgram.web.service;

import ru.kiselgram.web.model.Report;
import ru.kiselgram.web.model.User;
import ru.kiselgram.web.model.LoginOtp;
import ru.kiselgram.web.model.EmailVerification;
import ru.kiselgram.web.repository.UserRepository;
import org.hibernate.Session;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.*;

import static ru.kiselgram.web.config.HibernateConfig.getInstance;

public class AdminService {

    private final UserRepository userRepository;

    public AdminService() {
        this.userRepository = new UserRepository();
    }

    public AdminService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    public Map<String, Object> getDashboardStats() {
        Map<String, Object> stats = new HashMap<>();

        Session session = getInstance().getSession();

        Long totalUsers = session.createQuery(
                "SELECT COUNT(u) FROM User u WHERE u.isDeleted = false", Long.class).uniqueResult();
        stats.put("total_users", totalUsers != null ? totalUsers : 0L);

        Long totalMessages = session.createQuery(
                "SELECT COUNT(m) FROM Message m", Long.class).uniqueResult();
        stats.put("total_messages", totalMessages != null ? totalMessages : 0L);

        Long totalChats = session.createQuery(
                "SELECT COUNT(c) FROM Chat c", Long.class).uniqueResult();
        stats.put("total_chats", totalChats != null ? totalChats : 0L);

        Long totalGroups = session.createQuery(
                "SELECT COUNT(c) FROM Chat c WHERE c.chatType = 'group'", Long.class).uniqueResult();
        stats.put("total_groups", totalGroups != null ? totalGroups : 0L);

        Long totalChannels = session.createQuery(
                "SELECT COUNT(c) FROM Chat c WHERE c.chatType = 'channel'", Long.class).uniqueResult();
        stats.put("total_channels", totalChannels != null ? totalChannels : 0L);

        Long onlineUsers = session.createQuery(
                "SELECT COUNT(u) FROM User u WHERE u.isOnline = true AND u.isDeleted = false", Long.class).uniqueResult();
        stats.put("online_users", onlineUsers != null ? onlineUsers : 0L);

        Long totalReports = session.createQuery(
                "SELECT COUNT(r) FROM Report r WHERE r.status = 'pending'", Long.class).uniqueResult();
        stats.put("pending_reports", totalReports != null ? totalReports : 0L);

        Long allReports = session.createQuery(
                "SELECT COUNT(r) FROM Report r", Long.class).uniqueResult();
        stats.put("total_reports", allReports != null ? allReports : 0L);

        Long usersToday = session.createQuery(
                "SELECT COUNT(u) FROM User u WHERE u.createdAt >= current_date AND u.isDeleted = false", Long.class).uniqueResult();
        stats.put("users_today", usersToday != null ? usersToday : 0L);

        return stats;
    }

    public List<Map<String, Object>> getUsers(int page, int perPage) {
        List<User> users = userRepository.findAll(page, perPage);
        return users.stream().map(User::toMap).toList();
    }

    public Map<String, Object> deleteUserByAdmin(Long adminId, Long userId) {
        try {
            User admin = userRepository.findById(adminId)
                    .orElseThrow(() -> new RuntimeException("Admin not found"));

            if (!admin.isAdmin()) {
                return errorMap("Only admins can delete users");
            }

            User user = userRepository.findById(userId)
                    .orElseThrow(() -> new RuntimeException("User not found"));

            user.setDeleted(true);
            user.setDeletedAt(LocalDateTime.now());
            userRepository.update(user);

            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            result.put("message", "User deleted successfully");
            return result;
        } catch (Exception e) {
            return errorMap("Failed to delete user: " + e.getMessage());
        }
    }

    public List<Map<String, Object>> getReports(int page, int perPage) {
        Session session = getInstance().getSession();
        List<Report> reports = session.createQuery(
                        "FROM Report r ORDER BY r.createdAt DESC", Report.class)
                .setFirstResult((page - 1) * perPage)
                .setMaxResults(perPage)
                .list();

        List<Map<String, Object>> result = new ArrayList<>();
        for (Report report : reports) {
            Map<String, Object> m = new HashMap<>();
            m.put("id", report.getId());
            m.put("reported_user_id", report.getReportedUserId());
            m.put("reported_by", report.getUser() != null ? report.getUser().getId() : null);
            m.put("reason", report.getReason());
            m.put("description", report.getDescription());
            m.put("resolved", "resolved".equals(report.getStatus()));
            m.put("created_at", report.getCreatedAt() != null ? report.getCreatedAt().toString() : null);
            result.add(m);
        }
        return result;
    }

    public Map<String, Object> resolveReport(Long reportId, Long adminId) {
        try {
            User admin = userRepository.findById(adminId)
                    .orElseThrow(() -> new RuntimeException("Admin not found"));

            if (!admin.isAdmin()) {
                return errorMap("Only admins can resolve reports");
            }

            Session session = getInstance().getSession();
            session.beginTransaction();
            try {
                Report report = session.get(Report.class, reportId);
                if (report == null) {
                    session.getTransaction().rollback();
                    return errorMap("Report not found");
                }
                report.setStatus("resolved");
                report.setResolvedBy(adminId);
                report.setResolvedAt(LocalDateTime.now());
                session.merge(report);
                session.getTransaction().commit();
            } catch (Exception e) {
                session.getTransaction().rollback();
                throw e;
            }

            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            return result;
        } catch (Exception e) {
            return errorMap("Failed to resolve report: " + e.getMessage());
        }
    }

    public Map<String, Object> getTwofaOverview() {
        Session session = getInstance().getSession();

        Long total = session.createQuery(
                "SELECT COUNT(o) FROM LoginOtp o", Long.class).uniqueResult();

        Long active = session.createQuery(
                "SELECT COUNT(o) FROM LoginOtp o WHERE o.isUsed = false AND o.expiresAt > CURRENT_TIMESTAMP", Long.class).uniqueResult();

        Long expired = session.createQuery(
                "SELECT COUNT(o) FROM LoginOtp o WHERE o.expiresAt <= CURRENT_TIMESTAMP AND o.isUsed = false", Long.class).uniqueResult();

        Long used = session.createQuery(
                "SELECT COUNT(o) FROM LoginOtp o WHERE o.isUsed = true", Long.class).uniqueResult();

        LocalDateTime todayStart = LocalDate.now().atStartOfDay();
        Long sentToday = session.createQuery(
                "SELECT COUNT(o) FROM LoginOtp o WHERE o.createdAt >= :todayStart", Long.class)
                .setParameter("todayStart", todayStart)
                .uniqueResult();

        Map<String, Object> result = new HashMap<>();
        result.put("total", total != null ? total : 0L);
        result.put("active", active != null ? active : 0L);
        result.put("expired", expired != null ? expired : 0L);
        result.put("used", used != null ? used : 0L);
        result.put("sent_today", sentToday != null ? sentToday : 0L);
        return result;
    }

    public Map<String, Object> getOtps(int perPage) {
        Session session = getInstance().getSession();
        List<LoginOtp> otpList = session.createQuery(
                "FROM LoginOtp o ORDER BY o.createdAt DESC", LoginOtp.class)
                .setMaxResults(perPage)
                .list();

        Long total = session.createQuery(
                "SELECT COUNT(o) FROM LoginOtp o", Long.class).uniqueResult();

        List<Map<String, Object>> otps = new ArrayList<>();
        for (LoginOtp o : otpList) {
            String username = null;
            if (o.getUserId() != null) {
                User u = session.get(User.class, o.getUserId());
                if (u != null) username = u.getUsername();
            }
            Map<String, Object> m = new HashMap<>();
            m.put("id", o.getId());
            m.put("user_id", o.getUserId());
            m.put("username", username);
            m.put("code", o.getOtpCode());
            m.put("created_at", o.getCreatedAt() != null ? o.getCreatedAt().toString() : null);
            m.put("expires_at", o.getExpiresAt() != null ? o.getExpiresAt().toString() : null);
            m.put("used", o.isUsed());
            m.put("expired", o.getExpiresAt() != null && o.getExpiresAt().isBefore(LocalDateTime.now()) && !o.isUsed());
            otps.add(m);
        }

        Map<String, Object> result = new HashMap<>();
        result.put("otps", otps);
        long totalPages = (total != null && perPage > 0) ? (total + perPage - 1) / perPage : 1;
        result.put("page", 1);
        result.put("total_pages", totalPages);
        result.put("total", total != null ? total : 0L);
        return result;
    }

    public Map<String, Object> getEmailVerifications(int perPage) {
        Session session = getInstance().getSession();
        List<EmailVerification> verList = session.createQuery(
                "FROM EmailVerification e ORDER BY e.createdAt DESC", EmailVerification.class)
                .setMaxResults(perPage)
                .list();

        Long total = session.createQuery(
                "SELECT COUNT(e) FROM EmailVerification e", Long.class).uniqueResult();

        List<Map<String, Object>> codes = new ArrayList<>();
        for (EmailVerification e : verList) {
            String username = null;
            if (e.getUserId() != null) {
                User u = session.get(User.class, e.getUserId());
                if (u != null) username = u.getUsername();
            }
            Map<String, Object> m = new HashMap<>();
            m.put("id", e.getId());
            m.put("user_id", e.getUserId());
            m.put("username", username);
            m.put("email", e.getEmail());
            m.put("token", e.getVerificationCode());
            m.put("created_at", e.getCreatedAt() != null ? e.getCreatedAt().toString() : null);
            m.put("expires_at", e.getExpiresAt() != null ? e.getExpiresAt().toString() : null);
            m.put("verified", e.isVerified());
            m.put("expired", e.getExpiresAt() != null && e.getExpiresAt().isBefore(LocalDateTime.now()) && !e.isVerified());
            codes.add(m);
        }

        Map<String, Object> result = new HashMap<>();
        result.put("codes", codes);
        long totalPages = (total != null && perPage > 0) ? (total + perPage - 1) / perPage : 1;
        result.put("page", 1);
        result.put("total_pages", totalPages);
        result.put("total", total != null ? total : 0L);
        return result;
    }

    public Map<String, Object> cleanupOtps() {
        Session session = getInstance().getSession();
        session.beginTransaction();
        try {
            int deleted = session.createMutationQuery(
                    "DELETE FROM LoginOtp o WHERE o.expiresAt <= CURRENT_TIMESTAMP AND o.isUsed = false")
                    .executeUpdate();
            session.getTransaction().commit();
            return Map.of("success", true, "data", Map.of("deleted", deleted));
        } catch (Exception e) {
            session.getTransaction().rollback();
            return errorMap("Cleanup failed: " + e.getMessage());
        }
    }

    public Map<String, Object> cleanupEmailVerifications() {
        Session session = getInstance().getSession();
        session.beginTransaction();
        try {
            int deleted = session.createMutationQuery(
                    "DELETE FROM EmailVerification e WHERE e.expiresAt <= CURRENT_TIMESTAMP AND e.isVerified = false")
                    .executeUpdate();
            session.getTransaction().commit();
            return Map.of("success", true, "data", Map.of("deleted", deleted));
        } catch (Exception e) {
            session.getTransaction().rollback();
            return errorMap("Cleanup failed: " + e.getMessage());
        }
    }

    public Map<String, Object> createUser(String username, String email, String password) {
        if (username == null || username.isBlank()) return errorMap("Username required");
        if (email == null || email.isBlank()) return errorMap("Email required");
        if (password == null || password.length() < 6) return errorMap("Password must be at least 6 characters");
        if (userRepository.existsByUsername(username)) return errorMap("Username already taken");
        if (userRepository.existsByEmail(email)) return errorMap("Email already registered");
        User user = new User();
        user.setUsername(username);
        user.setEmail(email);
        user.setPassword(password);
        user.setEmailVerified(true);
        userRepository.save(user);
        return Map.of("success", true, "id", user.getId());
    }

    public Map<String, Object> updateUser(Long userId, String username, String email) {
        User user = userRepository.findById(userId).orElse(null);
        if (user == null) return errorMap("User not found");
        if (username != null && !username.isBlank()) user.setUsername(username);
        if (email != null && !email.isBlank()) user.setEmail(email);
        userRepository.update(user);
        return Map.of("success", true);
    }

    public Map<String, Object> setUserPassword(Long userId, String password) {
        if (password == null || password.length() < 6) return errorMap("Password must be at least 6 characters");
        User user = userRepository.findById(userId).orElse(null);
        if (user == null) return errorMap("User not found");
        user.setPassword(password);
        userRepository.update(user);
        return Map.of("success", true);
    }

    public Map<String, Object> toggleAdmin(Long adminId, Long userId) {
        User admin = userRepository.findById(adminId).orElse(null);
        if (admin == null || !admin.isAdmin()) return errorMap("Only admins can toggle admin status");
        if (adminId.equals(userId)) return errorMap("Cannot change your own admin status");
        User user = userRepository.findById(userId).orElse(null);
        if (user == null) return errorMap("User not found");
        user.setAdmin(!user.isAdmin());
        userRepository.update(user);
        return Map.of("success", true, "is_admin", user.isAdmin());
    }

    private Map<String, Object> errorMap(String message) {
        Map<String, Object> map = new HashMap<>();
        map.put("error", message);
        return map;
    }
}
