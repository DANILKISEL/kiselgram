package ru.kiselgram.web.model;

import ru.kiselgram.web.util.CryptoUtil;
import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

@Entity
@Table(name = "messages")
public class Message {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "_content", columnDefinition = "TEXT")
    private String _content;

    @Column(name = "sender_id", nullable = false)
    private Long senderId;

    @Column(name = "chat_id")
    private Long chatId;

    @Column(name = "receiver_id")
    private Long receiverId;

    @Column(nullable = false)
    private LocalDateTime timestamp;

    @Column(name = "is_read")
    private boolean isRead;

    @Column(name = "telegram_message_id", length = 50)
    private String telegramMessageId;

    @Column(name = "is_from_telegram")
    private boolean isFromTelegram;

    @Column(name = "delivered_at")
    private LocalDateTime deliveredAt;

    @Column(name = "read_at")
    private LocalDateTime readAt;

    @Column(name = "is_saved")
    private boolean isSaved;

    @Column(name = "deleted_at")
    private LocalDateTime deletedAt;

    @Column(name = "has_attachment")
    private boolean hasAttachment;

    @Column(name = "file_type", length = 20)
    private String fileType;

    @Column(name = "file_name", length = 255)
    private String fileName;

    @Column(name = "file_path", length = 500)
    private String filePath;

    @Column(name = "thumbnail_path", length = 500)
    private String thumbnailPath;

    @Column(name = "file_size")
    private Integer fileSize;

    @Column(name = "is_encrypted")
    private boolean isEncrypted;

    @Column(name = "encrypted_content", columnDefinition = "TEXT")
    private String encryptedContent;

    @Column(name = "encryption_key_id")
    private Integer encryptionKeyId;

    @Column(name = "is_deleted")
    private boolean isDeleted;

    @Column(name = "deleted_for_all")
    private boolean deletedForAll;

    @Column(name = "scheduled_at")
    private LocalDateTime scheduledAt;

    @Column(name = "edited_at")
    private LocalDateTime editedAt;

    @Column(name = "file_id")
    private Long fileId;

    @Column(name = "poll_id")
    private Long pollId;

    @Column(name = "poll_question", columnDefinition = "TEXT")
    private String pollQuestion;

    @Column(name = "forwarded_from_id")
    private Long forwardedFromId;

    @Column(name = "forwarded_by_id")
    private Long forwardedById;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "sender_id", insertable = false, updatable = false)
    private User sender;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "receiver_id", insertable = false, updatable = false)
    private User receiver;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "chat_id", insertable = false, updatable = false)
    private Chat chat;

    @OneToMany(mappedBy = "message")
    private Set<Reaction> reactions = new HashSet<>();

    @OneToMany(mappedBy = "originalMessage")
    private Set<Reply> replies = new HashSet<>();

    @OneToMany(mappedBy = "originalMessage")
    private Set<Forward> forwards = new HashSet<>();

    @ManyToOne
    @JoinColumn(name = "file_id", insertable = false, updatable = false)
    private CmsFile file;

    public Message() {
        this.timestamp = LocalDateTime.now();
        this.isRead = false;
        this.hasAttachment = false;
        this.isFromTelegram = false;
        this.isEncrypted = false;
        this.isDeleted = false;
        this.deletedForAll = false;
        this.isSaved = false;
    }

    public Message(Long id, String content, Long senderId, Long chatId, Long receiverId,
                   LocalDateTime timestamp, boolean isRead, String telegramMessageId,
                   boolean isFromTelegram, LocalDateTime deliveredAt, LocalDateTime readAt,
                   boolean isSaved, LocalDateTime deletedAt, boolean hasAttachment,
                   String fileType, String fileName, String filePath, String thumbnailPath,
                   Integer fileSize, boolean isEncrypted, String encryptedContent,
                   Integer encryptionKeyId, boolean isDeleted, boolean deletedForAll,
                   LocalDateTime scheduledAt, LocalDateTime editedAt, Long fileId,
                   Long pollId, String pollQuestion, Long forwardedFromId, Long forwardedById) {
        this.id = id;
        this._content = content;
        this.senderId = senderId;
        this.chatId = chatId;
        this.receiverId = receiverId;
        this.timestamp = timestamp;
        this.isRead = isRead;
        this.telegramMessageId = telegramMessageId;
        this.isFromTelegram = isFromTelegram;
        this.deliveredAt = deliveredAt;
        this.readAt = readAt;
        this.isSaved = isSaved;
        this.deletedAt = deletedAt;
        this.hasAttachment = hasAttachment;
        this.fileType = fileType;
        this.fileName = fileName;
        this.filePath = filePath;
        this.thumbnailPath = thumbnailPath;
        this.fileSize = fileSize;
        this.isEncrypted = isEncrypted;
        this.encryptedContent = encryptedContent;
        this.encryptionKeyId = encryptionKeyId;
        this.isDeleted = isDeleted;
        this.deletedForAll = deletedForAll;
        this.scheduledAt = scheduledAt;
        this.editedAt = editedAt;
        this.fileId = fileId;
        this.pollId = pollId;
        this.pollQuestion = pollQuestion;
        this.forwardedFromId = forwardedFromId;
        this.forwardedById = forwardedById;
    }

    @Transient
    public String getContent() {
        if (_content != null) {
            return _content;
        }
        if (encryptedContent != null) {
            try {
                return CryptoUtil.getInstance().decryptMessage(encryptedContent);
            } catch (Exception e) {
                return null;
            }
        }
        return null;
    }

    public void setContent(String content) {
        this._content = content;
        if (isEncrypted && content != null) {
            try {
                this.encryptedContent = CryptoUtil.getInstance().encryptMessage(content);
                this._content = null;
            } catch (Exception e) {
                this._content = content;
            }
        }
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("id", id);
        map.put("content", getContent());
        map.put("sender_id", senderId);
        map.put("chat_id", chatId);
        map.put("receiver_id", receiverId);
        map.put("timestamp", timestamp);
        map.put("is_read", isRead);
        map.put("telegram_message_id", telegramMessageId);
        map.put("is_from_telegram", isFromTelegram);
        map.put("delivered_at", deliveredAt);
        map.put("read_at", readAt);
        map.put("is_saved", isSaved);
        map.put("deleted_at", deletedAt);
        map.put("has_attachment", hasAttachment);
        map.put("file_type", fileType);
        map.put("file_name", fileName);
        map.put("file_path", filePath);
        map.put("thumbnail_path", thumbnailPath);
        map.put("file_size", fileSize);
        map.put("is_encrypted", isEncrypted);
        map.put("encryption_key_id", encryptionKeyId);
        map.put("is_deleted", isDeleted);
        map.put("deleted_for_all", deletedForAll);
        map.put("scheduled_at", scheduledAt);
        map.put("edited_at", editedAt);
        map.put("file_id", fileId);
        map.put("poll_id", pollId);
        map.put("poll_question", pollQuestion);
        map.put("forwarded_from_id", forwardedFromId);
        map.put("forwarded_by_id", forwardedById);
        return map;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String get_content() { return _content; }
    public void set_content(String _content) { this._content = _content; }
    public Long getSenderId() { return senderId; }
    public void setSenderId(Long senderId) { this.senderId = senderId; }
    public Long getChatId() { return chatId; }
    public void setChatId(Long chatId) { this.chatId = chatId; }
    public Long getReceiverId() { return receiverId; }
    public void setReceiverId(Long receiverId) { this.receiverId = receiverId; }
    public LocalDateTime getTimestamp() { return timestamp; }
    public void setTimestamp(LocalDateTime timestamp) { this.timestamp = timestamp; }
    public boolean isRead() { return isRead; }
    public void setRead(boolean read) { isRead = read; }
    public String getTelegramMessageId() { return telegramMessageId; }
    public void setTelegramMessageId(String telegramMessageId) { this.telegramMessageId = telegramMessageId; }
    public boolean isFromTelegram() { return isFromTelegram; }
    public void setFromTelegram(boolean fromTelegram) { isFromTelegram = fromTelegram; }
    public LocalDateTime getDeliveredAt() { return deliveredAt; }
    public void setDeliveredAt(LocalDateTime deliveredAt) { this.deliveredAt = deliveredAt; }
    public LocalDateTime getReadAt() { return readAt; }
    public void setReadAt(LocalDateTime readAt) { this.readAt = readAt; }
    public boolean isSaved() { return isSaved; }
    public void setSaved(boolean saved) { isSaved = saved; }
    public LocalDateTime getDeletedAt() { return deletedAt; }
    public void setDeletedAt(LocalDateTime deletedAt) { this.deletedAt = deletedAt; }
    public boolean isHasAttachment() { return hasAttachment; }
    public void setHasAttachment(boolean hasAttachment) { this.hasAttachment = hasAttachment; }
    public String getFileType() { return fileType; }
    public void setFileType(String fileType) { this.fileType = fileType; }
    public String getFileName() { return fileName; }
    public void setFileName(String fileName) { this.fileName = fileName; }
    public String getFilePath() { return filePath; }
    public void setFilePath(String filePath) { this.filePath = filePath; }
    public String getThumbnailPath() { return thumbnailPath; }
    public void setThumbnailPath(String thumbnailPath) { this.thumbnailPath = thumbnailPath; }
    public Integer getFileSize() { return fileSize; }
    public void setFileSize(Integer fileSize) { this.fileSize = fileSize; }
    public boolean isEncrypted() { return isEncrypted; }
    public void setEncrypted(boolean encrypted) { isEncrypted = encrypted; }
    public String getEncryptedContent() { return encryptedContent; }
    public void setEncryptedContent(String encryptedContent) { this.encryptedContent = encryptedContent; }
    public Integer getEncryptionKeyId() { return encryptionKeyId; }
    public void setEncryptionKeyId(Integer encryptionKeyId) { this.encryptionKeyId = encryptionKeyId; }
    public boolean isDeleted() { return isDeleted; }
    public void setDeleted(boolean deleted) { isDeleted = deleted; }
    public boolean isDeletedForAll() { return deletedForAll; }
    public void setDeletedForAll(boolean deletedForAll) { this.deletedForAll = deletedForAll; }
    public LocalDateTime getScheduledAt() { return scheduledAt; }
    public void setScheduledAt(LocalDateTime scheduledAt) { this.scheduledAt = scheduledAt; }
    public LocalDateTime getEditedAt() { return editedAt; }
    public void setEditedAt(LocalDateTime editedAt) { this.editedAt = editedAt; }
    public Long getFileId() { return fileId; }
    public void setFileId(Long fileId) { this.fileId = fileId; }
    public Long getPollId() { return pollId; }
    public void setPollId(Long pollId) { this.pollId = pollId; }
    public String getPollQuestion() { return pollQuestion; }
    public void setPollQuestion(String pollQuestion) { this.pollQuestion = pollQuestion; }
    public Long getForwardedFromId() { return forwardedFromId; }
    public void setForwardedFromId(Long forwardedFromId) { this.forwardedFromId = forwardedFromId; }
    public Long getForwardedById() { return forwardedById; }
    public void setForwardedById(Long forwardedById) { this.forwardedById = forwardedById; }
    public Set<Reaction> getReactions() { return reactions; }
    public void setReactions(Set<Reaction> reactions) { this.reactions = reactions; }
    public Set<Reply> getReplies() { return replies; }
    public void setReplies(Set<Reply> replies) { this.replies = replies; }
    public Set<Forward> getForwards() { return forwards; }
    public void setForwards(Set<Forward> forwards) { this.forwards = forwards; }
    public CmsFile getFile() { return file; }
    public void setFile(CmsFile file) { this.file = file; }
    public User getSender() { return sender; }
    public void setSender(User sender) { this.sender = sender; }
    public User getReceiver() { return receiver; }
    public void setReceiver(User receiver) { this.receiver = receiver; }
    public Chat getChat() { return chat; }
    public void setChat(Chat chat) { this.chat = chat; }
}
