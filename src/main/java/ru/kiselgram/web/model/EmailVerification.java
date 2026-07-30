package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Entity
@Table(name = "email_verifications")
public class EmailVerification {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id")
    private Long userId;

    @Column(length = 100)
    private String email;

    @Column(name = "verification_code", length = 10)
    private String verificationCode;

    @Column(name = "is_verified")
    private boolean isVerified;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "expires_at")
    private LocalDateTime expiresAt;

    @Column(name = "verified_at")
    private LocalDateTime verifiedAt;

    public EmailVerification() {
        this.createdAt = LocalDateTime.now();
        this.isVerified = false;
    }

    public EmailVerification(Long id, Long userId, String email, String verificationCode,
                             boolean isVerified, LocalDateTime createdAt, LocalDateTime expiresAt,
                             LocalDateTime verifiedAt) {
        this.id = id;
        this.userId = userId;
        this.email = email;
        this.verificationCode = verificationCode;
        this.isVerified = isVerified;
        this.createdAt = createdAt;
        this.expiresAt = expiresAt;
        this.verifiedAt = verifiedAt;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("id", id);
        map.put("user_id", userId);
        map.put("email", email);
        map.put("is_verified", isVerified);
        map.put("created_at", createdAt);
        map.put("expires_at", expiresAt);
        map.put("verified_at", verifiedAt);
        return map;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getUserId() { return userId; }
    public void setUserId(Long userId) { this.userId = userId; }
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    public String getVerificationCode() { return verificationCode; }
    public void setVerificationCode(String verificationCode) { this.verificationCode = verificationCode; }
    public boolean isVerified() { return isVerified; }
    public void setVerified(boolean verified) { isVerified = verified; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    public LocalDateTime getExpiresAt() { return expiresAt; }
    public void setExpiresAt(LocalDateTime expiresAt) { this.expiresAt = expiresAt; }
    public LocalDateTime getVerifiedAt() { return verifiedAt; }
    public void setVerifiedAt(LocalDateTime verifiedAt) { this.verifiedAt = verifiedAt; }
}
