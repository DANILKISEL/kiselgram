package ru.kiselgram.web.config;

import org.hibernate.Session;
import org.hibernate.SessionFactory;
import org.hibernate.boot.MetadataSources;
import org.hibernate.boot.registry.StandardServiceRegistry;
import org.hibernate.boot.registry.StandardServiceRegistryBuilder;
import org.hibernate.cfg.Configuration;

public final class HibernateConfig {

    private static volatile HibernateConfig instance;
    private final SessionFactory sessionFactory;
    private final ThreadLocal<Session> currentSession = new ThreadLocal<>();

    private HibernateConfig() {
        AppConfig config = AppConfig.getInstance();
        String dbUrl = config.getDatabase().getUrl();
        boolean isH2 = dbUrl.contains("h2");

        Configuration cfg = new Configuration();

        if (isH2) {
            cfg.setProperty("hibernate.dialect", "org.hibernate.dialect.H2Dialect");
            cfg.setProperty("hibernate.connection.driver_class", "org.h2.Driver");
        } else {
            cfg.setProperty("hibernate.dialect", "org.hibernate.dialect.PostgreSQLDialect");
            cfg.setProperty("hibernate.connection.driver_class", "org.postgresql.Driver");
        }

        cfg.setProperty("hibernate.connection.url", dbUrl);
        cfg.setProperty("hibernate.connection.username", "sa");
        cfg.setProperty("hibernate.connection.password", "password");
        cfg.setProperty("hibernate.hbm2ddl.auto", "update");
        cfg.setProperty("hibernate.show_sql", String.valueOf(config.getDatabase().isEcho()));
        cfg.setProperty("hibernate.format_sql", "true");

        cfg.setProperty("hibernate.current_session_context_class", "thread");
        cfg.setProperty("hibernate.connection.pool_size", "10");

        StandardServiceRegistry registry = new StandardServiceRegistryBuilder()
                .applySettings(cfg.getProperties())
                .build();

        try {
            MetadataSources metadataSources = new MetadataSources(registry);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.User.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.UserPremium.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.Message.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.Chat.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.ChatMember.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.ChatSubscriber.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.GroupPermission.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.ChannelAdmin.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.CmsFile.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.Reaction.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.Reply.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.Forward.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.Story.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.StoryView.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.StoryLike.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.StoryReaction.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.StoryPrivacy.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.StoryAllowedUser.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.Contact.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.Call.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.VideoCall.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.VideoCallParticipant.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.BlockedUser.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.UserSession.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.Report.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.PushSubscription.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.Favorite.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.RecentSearch.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.PreloadedAvatar.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.PinnedChat.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.EmailVerification.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.UserMusic.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.UserKSettings.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.QrLoginToken.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.Referral.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.LoginOtp.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.Poll.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.PollVote.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.Pin.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.InviteLink.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.SavedMessage.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.Archive.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.ReadReceipt.class);
            metadataSources.addAnnotatedClass(ru.kiselgram.web.model.MusicTrack.class);
            sessionFactory = metadataSources.buildMetadata().buildSessionFactory();
        } catch (Exception e) {
            StandardServiceRegistryBuilder.destroy(registry);
            throw new RuntimeException("Failed to build SessionFactory", e);
        }
    }

    public static HibernateConfig getInstance() {
        if (instance == null) {
            synchronized (HibernateConfig.class) {
                if (instance == null) {
                    instance = new HibernateConfig();
                }
            }
        }
        return instance;
    }

    public SessionFactory getSessionFactory() {
        return sessionFactory;
    }

    public Session getSession() {
        Session session = currentSession.get();
        if (session == null || !session.isOpen()) {
            session = sessionFactory.openSession();
            currentSession.set(session);
        }
        return session;
    }

    public void close() {
        Session session = currentSession.get();
        if (session != null && session.isOpen()) {
            session.close();
            currentSession.remove();
        }
        if (sessionFactory != null && !sessionFactory.isClosed()) {
            sessionFactory.close();
        }
    }
}
