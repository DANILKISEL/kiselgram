package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Entity
@Table(name = "referrals")
public class Referral {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "referrer_id", nullable = false)
    private Long referrerId;

    @Column(name = "referred_id")
    private Long referredId;

    @Column(length = 50)
    private String code;

    @Column(length = 20)
    private String status;

    @Column(name = "is_rewarded")
    private boolean isRewarded;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    public Referral() {
        this.createdAt = LocalDateTime.now();
        this.isRewarded = false;
    }

    public Referral(Long id, Long referrerId, Long referredId, String code,
                    boolean isRewarded, LocalDateTime createdAt) {
        this.id = id;
        this.referrerId = referrerId;
        this.referredId = referredId;
        this.code = code;
        this.isRewarded = isRewarded;
        this.createdAt = createdAt;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("id", id);
        map.put("referrer_id", referrerId);
        map.put("referred_id", referredId);
        map.put("code", code);
        map.put("is_rewarded", isRewarded);
        map.put("created_at", createdAt);
        return map;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getReferrerId() { return referrerId; }
    public void setReferrerId(Long referrerId) { this.referrerId = referrerId; }
    public Long getReferredId() { return referredId; }
    public void setReferredId(Long referredId) { this.referredId = referredId; }
    public String getCode() { return code; }
    public void setCode(String code) { this.code = code; }
    public boolean isRewarded() { return isRewarded; }
    public void setRewarded(boolean rewarded) { isRewarded = rewarded; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
