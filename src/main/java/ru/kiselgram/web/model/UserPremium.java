package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Entity
@Table(name = "user_premium")
public class UserPremium {

    @Id
    private Long userId;

    @OneToOne
    @MapsId
    @JoinColumn(name = "user_id")
    private User user;

    @Column(name = "is_premium")
    private boolean isPremium;

    @Column(name = "premium_since")
    private LocalDateTime premiumSince;

    @Column(name = "premium_expires_at")
    private LocalDateTime premiumExpiresAt;

    @Column(name = "premium_auto_renew")
    private boolean premiumAutoRenew;

    @Column(name = "premium_payment_method", length = 50)
    private String premiumPaymentMethod;

    @Column(name = "premium_plan", length = 50)
    private String premiumPlan;

    public UserPremium() {}

    public UserPremium(Long userId, User user, boolean isPremium, LocalDateTime premiumSince,
                       LocalDateTime premiumExpiresAt, boolean premiumAutoRenew,
                       String premiumPaymentMethod, String premiumPlan) {
        this.userId = userId;
        this.user = user;
        this.isPremium = isPremium;
        this.premiumSince = premiumSince;
        this.premiumExpiresAt = premiumExpiresAt;
        this.premiumAutoRenew = premiumAutoRenew;
        this.premiumPaymentMethod = premiumPaymentMethod;
        this.premiumPlan = premiumPlan;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("user_id", userId);
        map.put("is_premium", isPremium);
        map.put("premium_since", premiumSince);
        map.put("premium_expires_at", premiumExpiresAt);
        map.put("premium_auto_renew", premiumAutoRenew);
        map.put("premium_payment_method", premiumPaymentMethod);
        map.put("premium_plan", premiumPlan);
        return map;
    }

    public Long getUserId() { return userId; }
    public void setUserId(Long userId) { this.userId = userId; }
    public User getUser() { return user; }
    public void setUser(User user) { this.user = user; }
    public boolean isPremium() { return isPremium; }
    public void setPremium(boolean premium) { isPremium = premium; }
    public LocalDateTime getPremiumSince() { return premiumSince; }
    public void setPremiumSince(LocalDateTime premiumSince) { this.premiumSince = premiumSince; }
    public LocalDateTime getPremiumExpiresAt() { return premiumExpiresAt; }
    public void setPremiumExpiresAt(LocalDateTime premiumExpiresAt) { this.premiumExpiresAt = premiumExpiresAt; }
    public boolean isPremiumAutoRenew() { return premiumAutoRenew; }
    public void setPremiumAutoRenew(boolean premiumAutoRenew) { this.premiumAutoRenew = premiumAutoRenew; }
    public String getPremiumPaymentMethod() { return premiumPaymentMethod; }
    public void setPremiumPaymentMethod(String premiumPaymentMethod) { this.premiumPaymentMethod = premiumPaymentMethod; }
    public String getPremiumPlan() { return premiumPlan; }
    public void setPremiumPlan(String premiumPlan) { this.premiumPlan = premiumPlan; }
}
