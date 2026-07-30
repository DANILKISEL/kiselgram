package ru.kiselgram.web.repository;

import ru.kiselgram.web.config.HibernateConfig;
import jakarta.persistence.criteria.CriteriaBuilder;
import jakarta.persistence.criteria.CriteriaQuery;
import org.hibernate.Session;
import org.hibernate.Transaction;

import java.lang.reflect.ParameterizedType;
import java.util.List;
import java.util.Optional;

public abstract class GenericRepository<T> {

    protected final Class<T> entityClass;

    @SuppressWarnings("unchecked")
    public GenericRepository() {
        this.entityClass = (Class<T>) ((ParameterizedType) getClass()
                .getGenericSuperclass()).getActualTypeArguments()[0];
    }

    protected Session getSession() {
        return HibernateConfig.getInstance().getSession();
    }

    public Optional<T> findById(Long id) {
        Session session = getSession();
        T entity = session.get(entityClass, id);
        return Optional.ofNullable(entity);
    }

    public List<T> findAll() {
        Session session = getSession();
        CriteriaBuilder cb = session.getCriteriaBuilder();
        CriteriaQuery<T> cq = cb.createQuery(entityClass);
        cq.select(cq.from(entityClass));
        return session.createQuery(cq).list();
    }

    public List<T> findAll(int page, int perPage) {
        Session session = getSession();
        CriteriaBuilder cb = session.getCriteriaBuilder();
        CriteriaQuery<T> cq = cb.createQuery(entityClass);
        cq.select(cq.from(entityClass));
        return session.createQuery(cq)
                .setFirstResult((page - 1) * perPage)
                .setMaxResults(perPage)
                .list();
    }

    public long count() {
        Session session = getSession();
        CriteriaBuilder cb = session.getCriteriaBuilder();
        CriteriaQuery<Long> cq = cb.createQuery(Long.class);
        cq.select(cb.count(cq.from(entityClass)));
        return session.createQuery(cq).uniqueResult();
    }

    public T save(T entity) {
        Session session = getSession();
        Transaction tx = session.beginTransaction();
        try {
            session.persist(entity);
            tx.commit();
            return entity;
        } catch (Exception e) {
            tx.rollback();
            throw new RuntimeException("Failed to save entity", e);
        }
    }

    public T update(T entity) {
        Session session = getSession();
        Transaction tx = session.beginTransaction();
        try {
            T merged = session.merge(entity);
            tx.commit();
            return merged;
        } catch (Exception e) {
            tx.rollback();
            throw new RuntimeException("Failed to update entity", e);
        }
    }

    public void delete(T entity) {
        Session session = getSession();
        Transaction tx = session.beginTransaction();
        try {
            session.remove(entity);
            tx.commit();
        } catch (Exception e) {
            tx.rollback();
            throw new RuntimeException("Failed to delete entity", e);
        }
    }

    public void deleteById(Long id) {
        findById(id).ifPresent(this::delete);
    }
}
