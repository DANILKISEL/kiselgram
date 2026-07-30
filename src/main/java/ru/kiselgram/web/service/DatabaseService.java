package ru.kiselgram.web.service;

import ru.kiselgram.web.config.HibernateConfig;
import org.hibernate.SessionFactory;

public class DatabaseService {

    private static final DatabaseService INSTANCE = new DatabaseService();

    private DatabaseService() {}

    public static DatabaseService getInstance() {
        return INSTANCE;
    }

    public SessionFactory getSessionFactory() {
        return HibernateConfig.getInstance().getSessionFactory();
    }
}
