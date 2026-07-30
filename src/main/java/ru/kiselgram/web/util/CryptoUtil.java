package ru.kiselgram.web.util;

import javax.crypto.Cipher;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.util.Base64;

public final class CryptoUtil {

    public static String ENCRYPTION_KEY = null;

    private static final String AES_GCM_ALGORITHM = "AES/GCM/NoPadding";
    private static final int GCM_IV_LENGTH = 12;
    private static final int GCM_TAG_LENGTH = 128;
    private static final String ENC_PREFIX = "enc$1:";
    private static final int KEY_LENGTH_BYTES = 32;

    private static volatile CryptoUtil instance;
    private SecretKey secretKey;

    private CryptoUtil() {
        loadKey();
    }

    public static CryptoUtil getInstance() {
        if (instance == null) {
            synchronized (CryptoUtil.class) {
                if (instance == null) {
                    instance = new CryptoUtil();
                }
            }
        }
        return instance;
    }

    private void loadKey() {
        String keyStr = ENCRYPTION_KEY;
        if (keyStr == null || keyStr.isBlank()) {
            keyStr = System.getenv("MESSAGE_ENCRYPTION_KEY");
        }
        if (keyStr == null || keyStr.isBlank()) {
            SecureRandom rng = new SecureRandom();
            byte[] keyBytes = new byte[KEY_LENGTH_BYTES];
            rng.nextBytes(keyBytes);
            secretKey = new SecretKeySpec(keyBytes, "AES");
            return;
        }
        byte[] decoded = Base64.getDecoder().decode(keyStr);
        if (decoded.length != KEY_LENGTH_BYTES) {
            byte[] padded = new byte[KEY_LENGTH_BYTES];
            System.arraycopy(decoded, 0, padded, 0, Math.min(decoded.length, KEY_LENGTH_BYTES));
            decoded = padded;
        }
        secretKey = new SecretKeySpec(decoded, "AES");
    }

    public synchronized void reloadKey(String keyBase64) {
        ENCRYPTION_KEY = keyBase64;
        loadKey();
    }

    public String encryptMessage(String plaintext) {
        if (plaintext == null || plaintext.isEmpty()) {
            return plaintext;
        }
        try {
            SecureRandom rng = new SecureRandom();
            byte[] iv = new byte[GCM_IV_LENGTH];
            rng.nextBytes(iv);

            Cipher cipher = Cipher.getInstance(AES_GCM_ALGORITHM);
            GCMParameterSpec spec = new GCMParameterSpec(GCM_TAG_LENGTH, iv);
            cipher.init(Cipher.ENCRYPT_MODE, secretKey, spec);

            byte[] ciphertext = cipher.doFinal(plaintext.getBytes(StandardCharsets.UTF_8));

            byte[] combined = new byte[GCM_IV_LENGTH + ciphertext.length];
            System.arraycopy(iv, 0, combined, 0, GCM_IV_LENGTH);
            System.arraycopy(ciphertext, 0, combined, GCM_IV_LENGTH, ciphertext.length);

            return ENC_PREFIX + Base64.getEncoder().encodeToString(combined);
        } catch (Exception e) {
            throw new RuntimeException("Encryption failed", e);
        }
    }

    public String decryptMessage(String ciphertext) {
        if (ciphertext == null || ciphertext.isEmpty()) {
            return ciphertext;
        }
        if (!ciphertext.startsWith(ENC_PREFIX)) {
            return ciphertext;
        }
        try {
            String b64Data = ciphertext.substring(ENC_PREFIX.length());
            byte[] combined = Base64.getDecoder().decode(b64Data);

            byte[] iv = new byte[GCM_IV_LENGTH];
            byte[] encrypted = new byte[combined.length - GCM_IV_LENGTH];
            System.arraycopy(combined, 0, iv, 0, GCM_IV_LENGTH);
            System.arraycopy(combined, GCM_IV_LENGTH, encrypted, 0, encrypted.length);

            Cipher cipher = Cipher.getInstance(AES_GCM_ALGORITHM);
            GCMParameterSpec spec = new GCMParameterSpec(GCM_TAG_LENGTH, iv);
            cipher.init(Cipher.DECRYPT_MODE, secretKey, spec);

            byte[] decrypted = cipher.doFinal(encrypted);
            return new String(decrypted, StandardCharsets.UTF_8);
        } catch (Exception e) {
            throw new RuntimeException("Decryption failed", e);
        }
    }
}
