package ru.kiselgram.web.repository;

import ru.kiselgram.web.model.Story;
import ru.kiselgram.web.model.StoryLike;
import ru.kiselgram.web.model.StoryView;
import jakarta.persistence.criteria.CriteriaBuilder;
import jakarta.persistence.criteria.CriteriaQuery;
import jakarta.persistence.criteria.Root;
import org.hibernate.Session;
import org.hibernate.Transaction;
import org.hibernate.query.Query;

import java.time.LocalDateTime;
import java.util.List;

public class StoryRepository extends GenericRepository<Story> {

    public List<Story> getActiveStories(Long userId) {
        Session session = getSession();
        LocalDateTime cutoff = LocalDateTime.now().minusHours(24);
        Query<Story> q = session.createQuery(
                "FROM Story s WHERE s.user.id = :userId AND s.createdAt >= :cutoff " +
                        "ORDER BY s.createdAt DESC", Story.class);
        q.setParameter("userId", userId);
        q.setParameter("cutoff", cutoff);
        return q.list();
    }

    public List<Story> getExpiredStories() {
        Session session = getSession();
        LocalDateTime cutoff = LocalDateTime.now().minusHours(24);
        Query<Story> q = session.createQuery(
                "FROM Story s WHERE s.createdAt < :cutoff", Story.class);
        q.setParameter("cutoff", cutoff);
        return q.list();
    }

    public boolean hasActiveStory(Long userId) {
        Session session = getSession();
        LocalDateTime cutoff = LocalDateTime.now().minusHours(24);
        Query<Long> q = session.createQuery(
                "SELECT COUNT(s) FROM Story s WHERE s.user.id = :userId AND s.createdAt >= :cutoff",
                Long.class);
        q.setParameter("userId", userId);
        q.setParameter("cutoff", cutoff);
        return q.uniqueResult() > 0;
    }

    public StoryView addView(StoryView view) {
        Session session = getSession();
        Transaction tx = session.beginTransaction();
        try {
            session.persist(view);
            tx.commit();
            return view;
        } catch (Exception e) {
            tx.rollback();
            throw new RuntimeException("Failed to add story view", e);
        }
    }

    public StoryLike addLike(StoryLike like) {
        Session session = getSession();
        Transaction tx = session.beginTransaction();
        try {
            session.persist(like);
            tx.commit();
            return like;
        } catch (Exception e) {
            tx.rollback();
            throw new RuntimeException("Failed to add story like", e);
        }
    }
}
