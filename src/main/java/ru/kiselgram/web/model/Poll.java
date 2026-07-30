package ru.kiselgram.web.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

@Entity
@Table(name = "polls")
public class Poll {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String question;

    @ElementCollection
    @CollectionTable(name = "poll_options", joinColumns = @JoinColumn(name = "poll_id"))
    @Column(name = "option_text", columnDefinition = "TEXT")
    private Set<String> options = new HashSet<>();

    @Column(name = "is_anonymous")
    private boolean isAnonymous;

    @Column(name = "is_multiple_choice")
    private boolean isMultipleChoice;

    @Column(name = "allows_multiple_answers")
    private boolean allowsMultipleAnswers;

    @Column(name = "is_quiz")
    private boolean isQuiz;

    @Column(name = "correct_option_id")
    private Integer correctOptionId;

    @Column(name = "total_votes")
    private Integer totalVotes;

    @Column(name = "created_by", nullable = false)
    private Long createdBy;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "expires_at")
    private LocalDateTime expiresAt;

    @Column(name = "is_closed")
    private boolean isClosed;

    @OneToMany(mappedBy = "poll")
    private Set<PollVote> votes = new HashSet<>();

    public Poll() {
        this.createdAt = LocalDateTime.now();
        this.totalVotes = 0;
        this.isClosed = false;
        this.isAnonymous = true;
        this.isMultipleChoice = false;
        this.allowsMultipleAnswers = false;
        this.isQuiz = false;
    }

    public Poll(Long id, String question, Set<String> options, boolean isAnonymous,
                boolean isMultipleChoice, boolean allowsMultipleAnswers, boolean isQuiz,
                Integer correctOptionId, Integer totalVotes, Long createdBy,
                LocalDateTime createdAt, LocalDateTime expiresAt, boolean isClosed) {
        this.id = id;
        this.question = question;
        this.options = options;
        this.isAnonymous = isAnonymous;
        this.isMultipleChoice = isMultipleChoice;
        this.allowsMultipleAnswers = allowsMultipleAnswers;
        this.isQuiz = isQuiz;
        this.correctOptionId = correctOptionId;
        this.totalVotes = totalVotes;
        this.createdBy = createdBy;
        this.createdAt = createdAt;
        this.expiresAt = expiresAt;
        this.isClosed = isClosed;
    }

    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("id", id);
        map.put("question", question);
        map.put("options", options);
        map.put("is_anonymous", isAnonymous);
        map.put("is_multiple_choice", isMultipleChoice);
        map.put("allows_multiple_answers", allowsMultipleAnswers);
        map.put("is_quiz", isQuiz);
        map.put("correct_option_id", correctOptionId);
        map.put("total_votes", totalVotes);
        map.put("created_by", createdBy);
        map.put("created_at", createdAt);
        map.put("expires_at", expiresAt);
        map.put("is_closed", isClosed);
        return map;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getQuestion() { return question; }
    public void setQuestion(String question) { this.question = question; }
    public Set<String> getOptions() { return options; }
    public void setOptions(Set<String> options) { this.options = options; }
    public boolean isAnonymous() { return isAnonymous; }
    public void setAnonymous(boolean anonymous) { isAnonymous = anonymous; }
    public boolean isMultipleChoice() { return isMultipleChoice; }
    public void setMultipleChoice(boolean multipleChoice) { isMultipleChoice = multipleChoice; }
    public boolean isAllowsMultipleAnswers() { return allowsMultipleAnswers; }
    public void setAllowsMultipleAnswers(boolean allowsMultipleAnswers) { this.allowsMultipleAnswers = allowsMultipleAnswers; }
    public boolean isQuiz() { return isQuiz; }
    public void setQuiz(boolean quiz) { isQuiz = quiz; }
    public Integer getCorrectOptionId() { return correctOptionId; }
    public void setCorrectOptionId(Integer correctOptionId) { this.correctOptionId = correctOptionId; }
    public Integer getTotalVotes() { return totalVotes; }
    public void setTotalVotes(Integer totalVotes) { this.totalVotes = totalVotes; }
    public Long getCreatedBy() { return createdBy; }
    public void setCreatedBy(Long createdBy) { this.createdBy = createdBy; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    public LocalDateTime getExpiresAt() { return expiresAt; }
    public void setExpiresAt(LocalDateTime expiresAt) { this.expiresAt = expiresAt; }
    public boolean isClosed() { return isClosed; }
    public void setClosed(boolean closed) { isClosed = closed; }
    public Set<PollVote> getVotes() { return votes; }
    public void setVotes(Set<PollVote> votes) { this.votes = votes; }
}
