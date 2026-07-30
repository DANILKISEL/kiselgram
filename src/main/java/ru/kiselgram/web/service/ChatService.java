package ru.kiselgram.web.service;

import ru.kiselgram.web.model.*;
import ru.kiselgram.web.repository.*;
import org.hibernate.Session;

import java.time.LocalDateTime;
import java.util.*;

import static ru.kiselgram.web.config.HibernateConfig.getInstance;

public class ChatService {

    private final ChatRepository chatRepository;
    private final UserRepository userRepository;
    private final MessageRepository messageRepository;

    public ChatService() {
        this.chatRepository = new ChatRepository();
        this.userRepository = new UserRepository();
        this.messageRepository = new MessageRepository();
    }

    public ChatService(ChatRepository chatRepository,
                       UserRepository userRepository,
                       MessageRepository messageRepository) {
        this.chatRepository = chatRepository;
        this.userRepository = userRepository;
        this.messageRepository = messageRepository;
    }

    public List<Map<String, Object>> getChatList(Long userId, int page, int perPage) {
        List<Chat> chats = chatRepository.getUserChats(userId);
        List<Map<String, Object>> result = new ArrayList<>();

        for (Chat chat : chats) {
            Map<String, Object> item = chat.toMap();

            if ("personal".equals(chat.getChatType())) {
                Long otherId = chat.getUser1Id().equals(userId) ? chat.getUser2Id() : chat.getUser1Id();
                userRepository.findById(otherId).ifPresent(other -> {
                    item.put("other_user", other.toMap());
                    item.put("title", other.getDisplayName() != null ? other.getDisplayName() : other.getUsername());
                });
            }

            Message lastMsg = messageRepository.getLastMessageForChat(chat.getId());
            if (lastMsg != null) {
                item.put("last_message", messageToMap(lastMsg));
            }

            result.add(item);
        }

        int start = (page - 1) * perPage;
        int end = Math.min(start + perPage, result.size());
        if (start >= result.size()) return List.of();
        return result.subList(start, end);
    }

    public Map<String, Object> createGroup(Long userId, String name, String description, List<Long> memberIds) {
        try {
            User owner = userRepository.findById(userId)
                    .orElseThrow(() -> new RuntimeException("Owner not found"));

            Chat group = new Chat();
            group.setChatType("group");
            group.setName(name);
            group.setDescription(description);
            group.setOwnerId(userId);
            group.setPublic(false);
            group.setInviteLink(UUID.randomUUID().toString().substring(0, 16));
            Chat savedGroup = chatRepository.save(group);

            ChatMember ownerMember = new ChatMember();
            ownerMember.setChat(savedGroup);
            ownerMember.setUser(owner);
            ownerMember.setRole("creator");
            chatRepository.addMember(ownerMember);

            if (memberIds != null) {
                for (Long mid : memberIds) {
                    userRepository.findById(mid).ifPresent(memberUser -> {
                        ChatMember cm = new ChatMember();
                        cm.setChat(savedGroup);
                        cm.setUser(memberUser);
                        cm.setRole("member");
                        chatRepository.addMember(cm);
                    });
                }
            }

            return savedGroup.toMap();
        } catch (Exception e) {
            return errorMap("Failed to create group: " + e.getMessage());
        }
    }

    public Map<String, Object> createChannel(Long userId, String name, String description) {
        try {
            Chat channel = new Chat();
            channel.setChatType("channel");
            channel.setName(name);
            channel.setDescription(description);
            channel.setOwnerId(userId);
            channel.setPublic(true);
            channel.setInviteLink(UUID.randomUUID().toString().substring(0, 16));
            channel = chatRepository.save(channel);

            User owner = userRepository.findById(userId)
                    .orElseThrow(() -> new RuntimeException("Owner not found"));

            ChatMember ownerMember = new ChatMember();
            ownerMember.setChat(channel);
            ownerMember.setUser(owner);
            ownerMember.setRole("admin");
            chatRepository.addMember(ownerMember);

            return channel.toMap();
        } catch (Exception e) {
            return errorMap("Failed to create channel: " + e.getMessage());
        }
    }

    public Map<String, Object> updateGroup(Long userId, Long groupId, Map<String, Object> updates) {
        try {
            Chat group = chatRepository.findGroupById(groupId)
                    .orElseThrow(() -> new RuntimeException("Group not found"));

            if (!group.getOwnerId().equals(userId)) {
                return errorMap("Only the group owner can update the group");
            }

            if (updates.containsKey("name")) {
                group.setName((String) updates.get("name"));
            }
            if (updates.containsKey("description")) {
                group.setDescription((String) updates.get("description"));
            }
            if (updates.containsKey("is_public")) {
                group.setPublic((Boolean) updates.get("is_public"));
            }

            group = chatRepository.update(group);
            return group.toMap();
        } catch (Exception e) {
            return errorMap("Failed to update group: " + e.getMessage());
        }
    }

    public Map<String, Object> updateChannel(Long userId, Long channelId, Map<String, Object> updates) {
        try {
            Chat channel = chatRepository.findChannelById(channelId)
                    .orElseThrow(() -> new RuntimeException("Channel not found"));

            if (!channel.getOwnerId().equals(userId)) {
                return errorMap("Only the channel owner can update the channel");
            }

            if (updates.containsKey("name")) {
                channel.setName((String) updates.get("name"));
            }
            if (updates.containsKey("description")) {
                channel.setDescription((String) updates.get("description"));
            }
            if (updates.containsKey("is_public")) {
                channel.setPublic((Boolean) updates.get("is_public"));
            }

            channel = chatRepository.update(channel);
            return channel.toMap();
        } catch (Exception e) {
            return errorMap("Failed to update channel: " + e.getMessage());
        }
    }

    public Map<String, Object> joinGroup(Long userId, String inviteLink) {
        try {
            Chat group = chatRepository.findByInviteLink(inviteLink)
                    .orElseThrow(() -> new RuntimeException("Group not found"));

            if (!"group".equals(group.getChatType())) {
                return errorMap("Invalid invite link");
            }

            User user = userRepository.findById(userId)
                    .orElseThrow(() -> new RuntimeException("User not found"));

            ChatMember member = new ChatMember();
            member.setChat(group);
            member.setUser(user);
            member.setRole("member");
            chatRepository.addMember(member);

            return group.toMap();
        } catch (Exception e) {
            return errorMap("Failed to join group: " + e.getMessage());
        }
    }

    public Map<String, Object> leaveGroup(Long userId, Long groupId) {
        try {
            chatRepository.removeMember(groupId, userId);
            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            return result;
        } catch (Exception e) {
            return errorMap("Failed to leave group: " + e.getMessage());
        }
    }

    public Map<String, Object> subscribe(Long userId, Long channelId) {
        try {
            Chat channel = chatRepository.findChannelById(channelId)
                    .orElseThrow(() -> new RuntimeException("Channel not found"));

            User user = userRepository.findById(userId)
                    .orElseThrow(() -> new RuntimeException("User not found"));

            ChatSubscriber subscriber = new ChatSubscriber();
            subscriber.setChat(channel);
            subscriber.setUser(user);
            chatRepository.addSubscriber(subscriber);

            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            result.put("channel_id", channelId);
            return result;
        } catch (Exception e) {
            return errorMap("Failed to subscribe: " + e.getMessage());
        }
    }

    public Map<String, Object> unsubscribe(Long userId, Long channelId) {
        try {
            chatRepository.removeSubscriber(channelId, userId);
            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            return result;
        } catch (Exception e) {
            return errorMap("Failed to unsubscribe: " + e.getMessage());
        }
    }

    public List<ChatMember> getGroupMembers(Long groupId, int page, int perPage) {
        Session session = getInstance().getSession();
        return session.createQuery(
                        "FROM ChatMember cm WHERE cm.chat.id = :groupId ORDER BY cm.joinedAt ASC",
                        ChatMember.class)
                .setParameter("groupId", groupId)
                .setFirstResult((page - 1) * perPage)
                .setMaxResults(perPage)
                .list();
    }

    public Map<String, Object> addContact(Long userId, Long contactId) {
        try {
            User user = userRepository.findById(userId)
                    .orElseThrow(() -> new RuntimeException("User not found"));
            User contact = userRepository.findById(contactId)
                    .orElseThrow(() -> new RuntimeException("Contact not found"));

            Session session = getInstance().getSession();
            session.beginTransaction();
            try {
                Contact c = new Contact();
                c.setUser(user);
                c.setContactUser(contact);
                session.persist(c);
                session.getTransaction().commit();
            } catch (Exception e) {
                session.getTransaction().rollback();
                if (e.getMessage() != null && e.getMessage().contains("unique")) {
                    return errorMap("Contact already exists");
                }
                throw e;
            }

            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            return result;
        } catch (Exception e) {
            return errorMap("Failed to add contact: " + e.getMessage());
        }
    }

    public Map<String, Object> removeContact(Long userId, Long contactId) {
        try {
            Session session = getInstance().getSession();
            session.beginTransaction();
            try {
                session.createQuery(
                                "DELETE FROM Contact c WHERE c.user.id = :userId AND c.contactUser.id = :contactId")
                        .setParameter("userId", userId)
                        .setParameter("contactId", contactId)
                        .executeUpdate();
                session.getTransaction().commit();
            } catch (Exception e) {
                session.getTransaction().rollback();
                throw e;
            }
            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            return result;
        } catch (Exception e) {
            return errorMap("Failed to remove contact: " + e.getMessage());
        }
    }

    public Map<String, Object> blockUser(Long userId, Long blockedUserId) {
        try {
            Session session = getInstance().getSession();
            session.beginTransaction();
            try {
                User blockingUser = userRepository.findById(userId)
                    .orElseThrow(() -> new RuntimeException("User not found"));
            User blocked = userRepository.findById(blockedUserId)
                    .orElseThrow(() -> new RuntimeException("Blocked user not found"));
            BlockedUser bu = new BlockedUser();
                bu.setUser(blockingUser);
                bu.setBlockedUser(blocked);
                session.persist(bu);
                session.getTransaction().commit();
            } catch (Exception e) {
                session.getTransaction().rollback();
                if (e.getMessage() != null && e.getMessage().contains("unique")) {
                    return errorMap("User already blocked");
                }
                throw e;
            }
            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            return result;
        } catch (Exception e) {
            return errorMap("Failed to block user: " + e.getMessage());
        }
    }

    public Map<String, Object> unblockUser(Long userId, Long blockedUserId) {
        try {
            Session session = getInstance().getSession();
            session.beginTransaction();
            try {
                session.createQuery(
                                "DELETE FROM BlockedUser b WHERE b.user.id = :userId AND b.blockedUser.id = :blockedId")
                        .setParameter("userId", userId)
                        .setParameter("blockedId", blockedUserId)
                        .executeUpdate();
                session.getTransaction().commit();
            } catch (Exception e) {
                session.getTransaction().rollback();
                throw e;
            }
            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            return result;
        } catch (Exception e) {
            return errorMap("Failed to unblock user: " + e.getMessage());
        }
    }

    private Map<String, Object> messageToMap(Message msg) {
        Map<String, Object> map = new HashMap<>();
        map.put("id", msg.getId());
        map.put("content", msg.getContent());
        map.put("sender_id", msg.getSenderId());
        map.put("timestamp", msg.getTimestamp().toString());
        map.put("is_read", msg.isRead());
        return map;
    }

    private Map<String, Object> errorMap(String message) {
        Map<String, Object> map = new HashMap<>();
        map.put("error", message);
        return map;
    }
}
