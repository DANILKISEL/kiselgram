package ru.kiselgram.web.service;

import ru.kiselgram.web.model.*;
import ru.kiselgram.web.repository.StoryRepository;
import ru.kiselgram.web.repository.UserRepository;
import org.hibernate.Session;

import java.time.LocalDateTime;
import java.util.*;

import static ru.kiselgram.web.config.HibernateConfig.getInstance;

public class StoryService {

    private final StoryRepository storyRepository;
    private final UserRepository userRepository;

    public StoryService() {
        this.storyRepository = new StoryRepository();
        this.userRepository = new UserRepository();
    }

    public StoryService(StoryRepository storyRepository, UserRepository userRepository) {
        this.storyRepository = storyRepository;
        this.userRepository = userRepository;
    }

    public Map<String, Object> createStory(Long userId, String mediaPath, String mediaType, String caption) {
        try {
            User user = userRepository.findById(userId)
                    .orElseThrow(() -> new RuntimeException("User not found"));

            Story story = new Story();
            story.setUser(user);
            story.setMediaPath(mediaPath);
            story.setMediaType(mediaType);
            story.setCaption(caption);
            story.setCreatedAt(LocalDateTime.now());
            story = storyRepository.save(story);

            return storyToMap(story);
        } catch (Exception e) {
            return errorMap("Failed to create story: " + e.getMessage());
        }
    }

    public Map<String, Object> getActiveStories(Long userId) {
        try {
            User user = userRepository.findById(userId)
                    .orElseThrow(() -> new RuntimeException("User not found"));

            List<Story> stories = storyRepository.getActiveStories(userId);
            List<Map<String, Object>> list = stories.stream().map(this::storyToMap).toList();

            Map<String, Object> result = new HashMap<>();
            result.put("stories", list);
            result.put("count", list.size());
            return result;
        } catch (Exception e) {
            return errorMap("Failed to get stories: " + e.getMessage());
        }
    }

    public void deleteExpiredStories() {
        List<Story> expired = storyRepository.getExpiredStories();
        for (Story story : expired) {
            storyRepository.delete(story);
        }
    }

    public Map<String, Object> viewStory(Long storyId, Long viewerId) {
        try {
            Story story = storyRepository.findById(storyId)
                    .orElseThrow(() -> new RuntimeException("Story not found"));
            User viewer = userRepository.findById(viewerId)
                    .orElseThrow(() -> new RuntimeException("Viewer not found"));

            StoryView view = new StoryView();
            view.setStory(story);
            view.setUser(viewer);
            view.setViewedAt(LocalDateTime.now());
            storyRepository.addView(view);

            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            return result;
        } catch (Exception e) {
            return errorMap("Failed to view story: " + e.getMessage());
        }
    }

    public Map<String, Object> likeStory(Long storyId, Long userId) {
        try {
            Story story = storyRepository.findById(storyId)
                    .orElseThrow(() -> new RuntimeException("Story not found"));
            User user = userRepository.findById(userId)
                    .orElseThrow(() -> new RuntimeException("User not found"));

            StoryLike like = new StoryLike();
            like.setStory(story);
            like.setUser(user);
            like.setCreatedAt(LocalDateTime.now());
            storyRepository.addLike(like);

            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            return result;
        } catch (Exception e) {
            return errorMap("Failed to like story: " + e.getMessage());
        }
    }

    private Map<String, Object> storyToMap(Story story) {
        Map<String, Object> map = new HashMap<>();
        map.put("id", story.getId());
        map.put("user_id", story.getUser().getId());
        map.put("media_path", story.getMediaPath());
        map.put("media_type", story.getMediaType());
        map.put("caption", story.getCaption());
        map.put("created_at", story.getCreatedAt().toString());
        return map;
    }

    private Map<String, Object> errorMap(String message) {
        Map<String, Object> map = new HashMap<>();
        map.put("error", message);
        return map;
    }
}
