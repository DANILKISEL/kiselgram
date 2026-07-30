package ru.kiselgram.web.service;

import ru.kiselgram.web.model.User;
import ru.kiselgram.web.repository.UserRepository;
import com.nimbusds.jwt.JWTClaimsSet;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.text.ParseException;
import java.util.Map;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AuthServiceTest {

    @Mock
    private UserRepository userRepository;

    private AuthService authService;

    @BeforeEach
    void setUp() {
        authService = new AuthService(userRepository);
    }

    @Test
    void register_createsUserAndReturnsToken() {
        when(userRepository.existsByUsername("testuser")).thenReturn(false);
        when(userRepository.existsByEmail("test@example.com")).thenReturn(false);
        when(userRepository.save(any())).thenAnswer(i -> {
            User u = i.getArgument(0);
            u.setId(1L);
            return u;
        });

        Map<String, Object> result = authService.register("testuser", "test@example.com", "password123");

        assertTrue(result.containsKey("session_token"));
        assertTrue(result.containsKey("user"));
        assertNotNull(result.get("session_token"));
        @SuppressWarnings("unchecked")
        Map<String, Object> userData = (Map<String, Object>) result.get("user");
        assertEquals("testuser", userData.get("username"));
        assertEquals("test@example.com", userData.get("email"));
    }

    @Test
    void register_duplicateUsername_returnsError() {
        when(userRepository.existsByUsername("taken")).thenReturn(true);

        Map<String, Object> result = authService.register("taken", "e@e.com", "pass");

        assertTrue(result.containsKey("error"));
        verify(userRepository, never()).save(any());
    }

    @Test
    void login_validCredentials_returnsTokenAndUser() {
        User user = new User();
        user.setId(1L);
        user.setUsername("testuser");
        user.setEmail("test@example.com");
        user.setPassword("correct");

        when(userRepository.findByUsername("testuser")).thenReturn(Optional.of(user));

        Map<String, Object> result = authService.login("testuser", "correct");

        assertTrue(result.containsKey("session_token"));
        @SuppressWarnings("unchecked")
        Map<String, Object> userData = (Map<String, Object>) result.get("user");
        assertEquals("testuser", userData.get("username"));
    }

    @Test
    void login_wrongPassword_returnsError() {
        User user = new User();
        user.setUsername("testuser");
        user.setPassword("correct");

        when(userRepository.findByUsername("testuser")).thenReturn(Optional.of(user));

        Map<String, Object> result = authService.login("testuser", "wrong");

        assertTrue(result.containsKey("error"));
    }

    @Test
    void login_unknownUser_returnsError() {
        when(userRepository.findByUsername("nobody")).thenReturn(Optional.empty());

        Map<String, Object> result = authService.login("nobody", "pass");

        assertTrue(result.containsKey("error"));
    }

    @Test
    void generateToken_and_validateToken_roundtrip() throws Exception {
        User user = new User();
        user.setId(42L);
        user.setUsername("tokenuser");

        String token = authService.generateToken(user);
        assertNotNull(token);
        assertFalse(token.isEmpty());

        JWTClaimsSet claims = authService.validateToken(token);
        assertNotNull(claims);
        assertEquals(42L, claims.getLongClaim("user_id"));
        assertEquals("tokenuser", claims.getStringClaim("username"));
    }

    @Test
    void validateToken_invalidToken_returnsNull() {
        JWTClaimsSet claims = authService.validateToken("invalid.jwt.token");
        assertNull(claims);
    }

    @Test
    void googleOAuth_exchangeFails_returnsError() throws Exception {
        AuthService spy = spy(authService);
        doReturn("{\"error\":\"invalid_grant\"}").when(spy).httpPost(anyString(), anyString());

        Map<String, Object> result = spy.googleOAuth("bad-code");

        assertTrue(result.containsKey("error"));
        assertTrue(((String) result.get("error")).contains("invalid_grant"));
    }

    @Test
    void googleOAuth_newUser_createsAndReturnsToken() throws Exception {
        AuthService spy = spy(authService);
        doReturn("{\"access_token\":\"tok123\"}").when(spy).httpPost(anyString(), anyString());
        doReturn("{\"id\":\"g123\",\"email\":\"guser@gmail.com\",\"name\":\"Google User\",\"picture\":\"https://pic\"}")
                .when(spy).httpGet(anyString(), anyString());

        when(userRepository.findByGoogleId("g123")).thenReturn(Optional.empty());
        when(userRepository.findByEmail("guser@gmail.com")).thenReturn(Optional.empty());
        when(userRepository.existsByUsername("guser")).thenReturn(false);
        when(userRepository.save(any())).thenAnswer(i -> {
            User u = i.getArgument(0);
            u.setId(99L);
            return u;
        });

        Map<String, Object> result = spy.googleOAuth("valid-code");

        assertTrue(result.containsKey("session_token"));
        @SuppressWarnings("unchecked")
        Map<String, Object> userData = (Map<String, Object>) result.get("user");
        assertEquals("guser", userData.get("username"));
        assertEquals("guser@gmail.com", userData.get("email"));

        verify(userRepository).save(argThat(u ->
                "g123".equals(u.getGoogleId()) &&
                "Google User".equals(u.getDisplayName()) &&
                "https://pic".equals(u.getAvatarUrl())
        ));
    }

    @Test
    void googleOAuth_existingUserByGoogleId_logsIn() throws Exception {
        User existing = new User();
        existing.setId(1L);
        existing.setUsername("existing");
        existing.setGoogleId("g123");

        AuthService spy = spy(authService);
        doReturn("{\"access_token\":\"tok123\"}").when(spy).httpPost(anyString(), anyString());
        doReturn("{\"id\":\"g123\",\"email\":\"old@gmail.com\",\"name\":\"Old\"}")
                .when(spy).httpGet(anyString(), anyString());

        when(userRepository.findByGoogleId("g123")).thenReturn(Optional.of(existing));

        Map<String, Object> result = spy.googleOAuth("code");

        assertTrue(result.containsKey("session_token"));
        verify(userRepository, never()).save(any());
    }

    @Test
    void loginByIdentifier_withUsername_returnsToken() {
        User user = new User();
        user.setId(2L);
        user.setUsername("byuser");
        user.setPassword("pass");

        when(userRepository.findByUsername("byuser")).thenReturn(Optional.of(user));

        Map<String, Object> result = authService.loginByIdentifier("byuser", "pass");

        assertTrue(result.containsKey("session_token"));
    }

    @Test
    void loginByIdentifier_withEmail_returnsToken() {
        User user = new User();
        user.setId(3L);
        user.setUsername("byemailuser");
        user.setEmail("by@e.com");
        user.setPassword("pass");

        when(userRepository.findByUsername("by@e.com")).thenReturn(Optional.empty());
        when(userRepository.findByEmail("by@e.com")).thenReturn(Optional.of(user));

        Map<String, Object> result = authService.loginByIdentifier("by@e.com", "pass");

        assertTrue(result.containsKey("session_token"));
    }

    @Test
    void loginByIdentifier_unknown_returnsError() {
        when(userRepository.findByUsername("x")).thenReturn(Optional.empty());
        when(userRepository.findByEmail("x")).thenReturn(Optional.empty());

        Map<String, Object> result = authService.loginByIdentifier("x", "p");

        assertTrue(result.containsKey("error"));
    }

    @Test
    void checkUsername_exists_returnsFalse() {
        when(userRepository.existsByUsername("taken")).thenReturn(true);
        assertFalse(authService.checkUsername("taken"));
    }

    @Test
    void checkUsername_free_returnsTrue() {
        when(userRepository.existsByUsername("free")).thenReturn(false);
        assertTrue(authService.checkUsername("free"));
    }

    @Test
    void logout_returnsSuccess() {
        Map<String, Object> result = authService.logout(1L);
        assertTrue((Boolean) result.get("success"));
    }
}
