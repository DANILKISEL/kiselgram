package ru.kiselgram.web.repository;

import ru.kiselgram.web.model.User;
import jakarta.persistence.criteria.CriteriaBuilder;
import jakarta.persistence.criteria.CriteriaQuery;
import jakarta.persistence.criteria.Predicate;
import jakarta.persistence.criteria.Root;
import org.hibernate.Session;
import org.hibernate.query.Query;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

public class UserRepository extends GenericRepository<User> {

    public Optional<User> findByUsername(String username) {
        Session session = getSession();
        Query<User> q = session.createQuery(
                "FROM User WHERE username = :username", User.class);
        q.setParameter("username", username);
        return q.uniqueResultOptional();
    }

    public Optional<User> findByEmail(String email) {
        Session session = getSession();
        Query<User> q = session.createQuery(
                "FROM User WHERE email = :email", User.class);
        q.setParameter("email", email);
        return q.uniqueResultOptional();
    }

    public Optional<User> findByGoogleId(String googleId) {
        Session session = getSession();
        Query<User> q = session.createQuery(
                "FROM User WHERE googleId = :googleId", User.class);
        q.setParameter("googleId", googleId);
        return q.uniqueResultOptional();
    }

    public boolean existsByUsername(String username) {
        return findByUsername(username).isPresent();
    }

    public boolean existsByEmail(String email) {
        return findByEmail(email).isPresent();
    }

    public List<User> findAllActive() {
        Session session = getSession();
        Query<User> q = session.createQuery(
                "FROM User WHERE isDeleted = false", User.class);
        return q.list();
    }

    public List<User> search(String query, int page, int perPage) {
        Session session = getSession();
        String pattern = "%" + query.toLowerCase() + "%";
        Query<User> q = session.createQuery(
                "FROM User WHERE (LOWER(username) LIKE :q OR LOWER(displayName) LIKE :q) " +
                        "AND isDeleted = false ORDER BY username", User.class);
        q.setParameter("q", pattern);
        q.setFirstResult((page - 1) * perPage);
        q.setMaxResults(perPage);
        return q.list();
    }

    public List<User> getContacts(Long userId, int page, int perPage) {
        Session session = getSession();
        Query<User> q = session.createQuery(
                "SELECT c.contactUser FROM Contact c WHERE c.user.id = :userId " +
                        "ORDER BY c.contactUser.username", User.class);
        q.setParameter("userId", userId);
        q.setFirstResult((page - 1) * perPage);
        q.setMaxResults(perPage);
        return q.list();
    }

    public List<Long> getBlockedUserIds(Long userId) {
        Session session = getSession();
        Query<Long> q = session.createQuery(
                "SELECT b.blockedUser.id FROM BlockedUser b WHERE b.user.id = :userId",
                Long.class);
        q.setParameter("userId", userId);
        return q.list();
    }

    public List<Long> getAllUserIdsWithMessages(Long userId) {
        Session session = getSession();
        Query<Long> q = session.createQuery(
                "SELECT DISTINCT CASE WHEN m.sender.id = :userId THEN m.receiver.id ELSE m.sender.id END " +
                        "FROM Message m WHERE m.sender.id = :userId OR m.receiver.id = :userId " +
                        "AND m.group IS NULL AND m.channel IS NULL", Long.class);
        q.setParameter("userId", userId);
        return q.list();
    }
}
