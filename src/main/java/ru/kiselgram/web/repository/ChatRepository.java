package ru.kiselgram.web.repository;

import ru.kiselgram.web.model.Chat;
import ru.kiselgram.web.model.ChatMember;
import ru.kiselgram.web.model.ChatSubscriber;
import org.hibernate.Session;
import org.hibernate.Transaction;
import org.hibernate.query.Query;

import java.util.List;
import java.util.Optional;

public class ChatRepository extends GenericRepository<Chat> {

    public Optional<Chat> findPersonalChat(Long user1Id, Long user2Id) {
        Session session = getSession();
        Query<Chat> q = session.createQuery(
                "FROM Chat c WHERE c.chatType = 'personal' AND " +
                        "((c.user1Id = :uid1 AND c.user2Id = :uid2) OR " +
                        "(c.user1Id = :uid2 AND c.user2Id = :uid1))", Chat.class);
        q.setParameter("uid1", user1Id);
        q.setParameter("uid2", user2Id);
        return q.uniqueResultOptional();
    }

    public Optional<Chat> findGroupById(Long id) {
        Session session = getSession();
        Query<Chat> q = session.createQuery(
                "FROM Chat c WHERE c.id = :id AND c.chatType = 'group'", Chat.class);
        q.setParameter("id", id);
        return q.uniqueResultOptional();
    }

    public Optional<Chat> findChannelById(Long id) {
        Session session = getSession();
        Query<Chat> q = session.createQuery(
                "FROM Chat c WHERE c.id = :id AND c.chatType = 'channel'", Chat.class);
        q.setParameter("id", id);
        return q.uniqueResultOptional();
    }

    public Optional<Chat> findByInviteLink(String link) {
        Session session = getSession();
        Query<Chat> q = session.createQuery(
                "FROM Chat c WHERE c.inviteLink = :link", Chat.class);
        q.setParameter("link", link);
        return q.uniqueResultOptional();
    }

    public List<Chat> getUserChats(Long userId) {
        Session session = getSession();
        Query<Chat> q = session.createQuery(
                "SELECT DISTINCT c FROM Chat c LEFT JOIN c.members m " +
                        "WHERE (c.chatType = 'personal' AND (c.user1Id = :uid OR c.user2Id = :uid)) " +
                        "OR (c.chatType IN ('group', 'channel') AND m.user.id = :uid) " +
                        "ORDER BY c.createdAt DESC", Chat.class);
        q.setParameter("uid", userId);
        return q.list();
    }

    public List<Chat> getUserGroups(Long userId) {
        Session session = getSession();
        Query<Chat> q = session.createQuery(
                "SELECT DISTINCT c FROM Chat c JOIN c.members m " +
                        "WHERE c.chatType = 'group' AND m.user.id = :userId " +
                        "ORDER BY c.name", Chat.class);
        q.setParameter("userId", userId);
        return q.list();
    }

    public List<Chat> getUserChannels(Long userId) {
        Session session = getSession();
        Query<Chat> q = session.createQuery(
                "SELECT DISTINCT c FROM Chat c JOIN c.subscribers s " +
                        "WHERE c.chatType = 'channel' AND s.user.id = :userId " +
                        "ORDER BY c.name", Chat.class);
        q.setParameter("userId", userId);
        return q.list();
    }

    public ChatMember addMember(ChatMember member) {
        Session session = getSession();
        Transaction tx = session.beginTransaction();
        try {
            session.persist(member);
            tx.commit();
            return member;
        } catch (Exception e) {
            tx.rollback();
            throw new RuntimeException("Failed to add chat member", e);
        }
    }

    public ChatSubscriber addSubscriber(ChatSubscriber subscriber) {
        Session session = getSession();
        Transaction tx = session.beginTransaction();
        try {
            session.persist(subscriber);
            tx.commit();
            return subscriber;
        } catch (Exception e) {
            tx.rollback();
            throw new RuntimeException("Failed to add chat subscriber", e);
        }
    }

    public void removeMember(Long chatId, Long userId) {
        Session session = getSession();
        Transaction tx = session.beginTransaction();
        try {
            Query<?> q = session.createQuery(
                    "DELETE FROM ChatMember m WHERE m.chat.id = :chatId AND m.user.id = :userId");
            q.setParameter("chatId", chatId);
            q.setParameter("userId", userId);
            q.executeUpdate();
            tx.commit();
        } catch (Exception e) {
            tx.rollback();
            throw new RuntimeException("Failed to remove chat member", e);
        }
    }

    public void removeSubscriber(Long chatId, Long userId) {
        Session session = getSession();
        Transaction tx = session.beginTransaction();
        try {
            Query<?> q = session.createQuery(
                    "DELETE FROM ChatSubscriber s WHERE s.chat.id = :chatId AND s.user.id = :userId");
            q.setParameter("chatId", chatId);
            q.setParameter("userId", userId);
            q.executeUpdate();
            tx.commit();
        } catch (Exception e) {
            tx.rollback();
            throw new RuntimeException("Failed to remove chat subscriber", e);
        }
    }

    public boolean isMember(Long chatId, Long userId) {
        Session session = getSession();
        Query<Long> q = session.createQuery(
                "SELECT COUNT(m) FROM ChatMember m WHERE m.chat.id = :chatId AND m.user.id = :userId",
                Long.class);
        q.setParameter("chatId", chatId);
        q.setParameter("userId", userId);
        return q.uniqueResult() > 0;
    }
}
