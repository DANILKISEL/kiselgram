package ru.kiselgram.web.repository;

import ru.kiselgram.web.model.Message;
import org.hibernate.Session;
import org.hibernate.query.Query;

import java.util.List;

public class MessageRepository extends GenericRepository<Message> {

    public List<Message> getPersonalMessages(Long userId1, Long userId2, Long afterId, int limit) {
        Session session = getSession();
        Query<Message> q = session.createQuery(
                "FROM Message m WHERE " +
                        "((m.sender.id = :uid1 AND m.receiver.id = :uid2) OR " +
                        "(m.sender.id = :uid2 AND m.receiver.id = :uid1)) " +
                        "AND m.id > :afterId AND m.chat IS NULL " +
                        "ORDER BY m.id ASC", Message.class);
        q.setParameter("uid1", userId1);
        q.setParameter("uid2", userId2);
        q.setParameter("afterId", afterId);
        if (limit > 0) q.setMaxResults(limit);
        return q.list();
    }

    public List<Message> getChatMessages(Long chatId, Long afterId, int limit) {
        Session session = getSession();
        Query<Message> q = session.createQuery(
                "FROM Message m WHERE m.chat.id = :chatId AND m.id > :afterId " +
                        "ORDER BY m.id ASC", Message.class);
        q.setParameter("chatId", chatId);
        q.setParameter("afterId", afterId);
        if (limit > 0) q.setMaxResults(limit);
        return q.list();
    }

    public Message getLastMessageForUser(Long currentUserId, Long otherUserId) {
        Session session = getSession();
        Query<Message> q = session.createQuery(
                "FROM Message m WHERE " +
                        "((m.sender.id = :uid1 AND m.receiver.id = :uid2) OR " +
                        "(m.sender.id = :uid2 AND m.receiver.id = :uid1)) " +
                        "AND m.chat IS NULL ORDER BY m.id DESC", Message.class);
        q.setParameter("uid1", currentUserId);
        q.setParameter("uid2", otherUserId);
        q.setMaxResults(1);
        return q.uniqueResult();
    }

    public Message getLastMessageForChat(Long chatId) {
        Session session = getSession();
        Query<Message> q = session.createQuery(
                "FROM Message m WHERE m.chat.id = :chatId ORDER BY m.id DESC",
                Message.class);
        q.setParameter("chatId", chatId);
        q.setMaxResults(1);
        return q.uniqueResult();
    }

    public long getUnreadCount(Long receiverId, Long senderId) {
        Session session = getSession();
        Query<Long> q = session.createQuery(
                "SELECT COUNT(m) FROM Message m WHERE m.receiver.id = :receiverId " +
                        "AND m.sender.id = :senderId AND m.isRead = false AND m.chat IS NULL",
                Long.class);
        q.setParameter("receiverId", receiverId);
        q.setParameter("senderId", senderId);
        return q.uniqueResult();
    }

    public long getUnreadCountForChat(Long chatId, Long userId) {
        Session session = getSession();
        Query<Long> q = session.createQuery(
                "SELECT COUNT(m) FROM Message m WHERE m.chat.id = :chatId " +
                        "AND m.sender.id != :userId AND m.isRead = false", Long.class);
        q.setParameter("chatId", chatId);
        q.setParameter("userId", userId);
        return q.uniqueResult();
    }

    public void markAsRead(Long senderId, Long receiverId) {
        Session session = getSession();
        session.beginTransaction();
        try {
            Query<?> q = session.createQuery(
                    "UPDATE Message m SET m.isRead = true WHERE m.sender.id = :senderId " +
                            "AND m.receiver.id = :receiverId AND m.isRead = false");
            q.setParameter("senderId", senderId);
            q.setParameter("receiverId", receiverId);
            q.executeUpdate();
            session.getTransaction().commit();
        } catch (Exception e) {
            session.getTransaction().rollback();
            throw new RuntimeException("Failed to mark messages as read", e);
        }
    }

    public List<Message> getLastMessageEachConversation(Long userId) {
        Session session = getSession();
        Query<Message> q = session.createQuery(
                "FROM Message m WHERE m.id IN (" +
                        "SELECT MAX(m2.id) FROM Message m2 WHERE " +
                        "(m2.sender.id = :userId OR m2.receiver.id = :userId) " +
                        "AND m2.chat IS NULL GROUP BY " +
                        "CASE WHEN m2.sender.id = :userId THEN m2.receiver.id ELSE m2.sender.id END" +
                        ") ORDER BY m.id DESC", Message.class);
        q.setParameter("userId", userId);
        return q.list();
    }

    public List<Message> getSavedMessages(Long userId, Long afterId, int limit) {
        Session session = getSession();
        Query<Message> q = session.createQuery(
                "FROM Message m WHERE m.receiver.id = :userId AND m.sender.id = :userId " +
                        "AND m.id > :afterId ORDER BY m.id DESC", Message.class);
        q.setParameter("userId", userId);
        q.setParameter("afterId", afterId);
        if (limit > 0) q.setMaxResults(limit);
        return q.list();
    }
}
