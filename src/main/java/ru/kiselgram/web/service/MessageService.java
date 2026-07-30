package ru.kiselgram.web.service;

import ru.kiselgram.web.model.*;
import ru.kiselgram.web.repository.*;
import org.hibernate.Session;

import java.time.LocalDateTime;
import java.util.*;

import static ru.kiselgram.web.config.HibernateConfig.getInstance;

public class MessageService {

    private final MessageRepository messageRepository;
    private final UserRepository userRepository;
    private final ChatRepository chatRepository;

    public MessageService() {
        this.messageRepository = new MessageRepository();
        this.userRepository = new UserRepository();
        this.chatRepository = new ChatRepository();
    }

    public MessageService(MessageRepository messageRepository,
                          UserRepository userRepository,
                          ChatRepository chatRepository) {
        this.messageRepository = messageRepository;
        this.userRepository = userRepository;
        this.chatRepository = chatRepository;
    }

    public Map<String, Object> sendMessage(Long senderId, Long receiverId, String content, Long replyToId) {
        try {
            Message message = new Message();
            message.setSenderId(senderId);
            message.setReceiverId(receiverId);
            message.setContent(content);
            message.setTimestamp(LocalDateTime.now());
            message.setRead(false);

            Optional<Chat> personalChat = chatRepository.findPersonalChat(senderId, receiverId);
            if (personalChat.isPresent()) {
                message.setChatId(personalChat.get().getId());
            }

            message = messageRepository.save(message);

            if (replyToId != null) {
                Session session = getInstance().getSession();
                session.beginTransaction();
                try {
                    Reply reply = new Reply();
                    reply.setOriginalMessage(session.getReference(Message.class, replyToId));
                    reply.setReplyMessageId(message.getId());
                    session.persist(reply);
                    session.getTransaction().commit();
                } catch (Exception e) {
                    session.getTransaction().rollback();
                }
            }

            return messageToMap(message);
        } catch (Exception e) {
            return errorMap("Failed to send message: " + e.getMessage());
        }
    }

    public Map<String, Object> sendGroupMessage(Long senderId, Long groupId, String content, Long replyToId) {
        try {
            if (!chatRepository.isMember(groupId, senderId)) {
                return errorMap("User is not a member of this group");
            }

            Message message = new Message();
            message.setSenderId(senderId);
            message.setReceiverId(senderId);
            message.setContent(content);
            message.setTimestamp(LocalDateTime.now());
            message.setRead(false);
            message.setChatId(groupId);

            message = messageRepository.save(message);

            if (replyToId != null) {
                Session session = getInstance().getSession();
                session.beginTransaction();
                try {
                    Reply reply = new Reply();
                    reply.setOriginalMessage(session.getReference(Message.class, replyToId));
                    reply.setReplyMessageId(message.getId());
                    session.persist(reply);
                    session.getTransaction().commit();
                } catch (Exception e) {
                    session.getTransaction().rollback();
                }
            }

            return messageToMap(message);
        } catch (Exception e) {
            return errorMap("Failed to send group message: " + e.getMessage());
        }
    }

    public Map<String, Object> sendChannelMessage(Long senderId, Long channelId, String content) {
        try {
            Message message = new Message();
            message.setSenderId(senderId);
            message.setReceiverId(senderId);
            message.setContent(content);
            message.setTimestamp(LocalDateTime.now());
            message.setRead(false);
            message.setChatId(channelId);

            message = messageRepository.save(message);
            return messageToMap(message);
        } catch (Exception e) {
            return errorMap("Failed to send channel message: " + e.getMessage());
        }
    }

    public Map<String, Object> editMessage(Long userId, Long messageId, String content) {
        try {
            Message message = messageRepository.findById(messageId)
                    .orElseThrow(() -> new RuntimeException("Message not found"));

            if (!message.getSenderId().equals(userId)) {
                return errorMap("Cannot edit another user's message");
            }

            message.setContent(content);
            message.setEditedAt(LocalDateTime.now());
            message = messageRepository.update(message);
            return messageToMap(message);
        } catch (Exception e) {
            return errorMap("Failed to edit message: " + e.getMessage());
        }
    }

    public Map<String, Object> deleteMessage(Long userId, Long messageId) {
        try {
            Message message = messageRepository.findById(messageId)
                    .orElseThrow(() -> new RuntimeException("Message not found"));

            if (!message.getSenderId().equals(userId)) {
                return errorMap("Cannot delete another user's message");
            }

            messageRepository.delete(message);
            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            return result;
        } catch (Exception e) {
            return errorMap("Failed to delete message: " + e.getMessage());
        }
    }

    public List<Map<String, Object>> getMessages(Long userId, Long peerId, Long afterId, int limit) {
        List<Message> messages = messageRepository.getPersonalMessages(userId, peerId, afterId, limit);
        return messages.stream().map(this::messageToMap).toList();
    }

    public List<Map<String, Object>> getGroupMessages(Long userId, Long groupId, Long afterId, int limit) {
        List<Message> messages = messageRepository.getChatMessages(groupId, afterId, limit);
        return messages.stream().map(this::messageToMap).toList();
    }

    public List<Map<String, Object>> getChannelMessages(Long userId, Long channelId, Long afterId, int limit) {
        List<Message> messages = messageRepository.getChatMessages(channelId, afterId, limit);
        return messages.stream().map(this::messageToMap).toList();
    }

    public Map<String, Object> addReaction(Long userId, Long messageId, String type) {
        try {
            Message message = messageRepository.findById(messageId)
                    .orElseThrow(() -> new RuntimeException("Message not found"));

            Session session = getInstance().getSession();
            session.beginTransaction();
            try {
                User user = userRepository.findById(userId)
                        .orElseThrow(() -> new RuntimeException("User not found"));

                Reaction reaction = new Reaction();
                reaction.setMessage(message);
                reaction.setUser(user);
                reaction.setReactionType(type);
                session.persist(reaction);
                session.getTransaction().commit();

                Map<String, Object> result = new HashMap<>();
                result.put("success", true);
                result.put("message_id", messageId);
                result.put("type", type);
                return result;
            } catch (Exception e) {
                session.getTransaction().rollback();
                return errorMap("Failed to add reaction: " + e.getMessage());
            }
        } catch (Exception e) {
            return errorMap("Failed to add reaction: " + e.getMessage());
        }
    }

    public List<Map<String, Object>> getReactions(Long messageId) {
        Session session = getInstance().getSession();
        List<Reaction> reactions = session.createQuery(
                        "FROM Reaction r WHERE r.message.id = :messageId", Reaction.class)
                .setParameter("messageId", messageId)
                .list();
        List<Map<String, Object>> result = new ArrayList<>();
        for (Reaction r : reactions) {
            Map<String, Object> m = new HashMap<>();
            m.put("user_id", r.getUser() != null ? r.getUser().getId() : null);
            m.put("type", r.getReactionType());
            result.add(m);
        }
        return result;
    }

    public void markRead(Long currentUserId, Long peerId) {
        messageRepository.markAsRead(peerId, currentUserId);
    }

    private Map<String, Object> messageToMap(Message message) {
        Map<String, Object> map = new HashMap<>();
        map.put("id", message.getId());
        map.put("content", message.getContent());
        map.put("sender_id", message.getSenderId());
        if (message.getReceiverId() != null) {
            map.put("receiver_id", message.getReceiverId());
        }
        map.put("timestamp", message.getTimestamp().toString());
        map.put("is_read", message.isRead());
        map.put("is_edited", message.getEditedAt() != null);
        if (message.getChatId() != null) {
            map.put("chat_id", message.getChatId());
        }
        return map;
    }

    private Map<String, Object> errorMap(String message) {
        Map<String, Object> map = new HashMap<>();
        map.put("error", message);
        return map;
    }
}
