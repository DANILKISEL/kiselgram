import os
from cryptography.fernet import Fernet

_KEY = None
_HAS_KEY = False

ENC_PREFIX = 'enc$1:'


def _get_key():
    global _KEY, _HAS_KEY
    if _HAS_KEY:
        return _KEY
    raw = os.environ.get('MESSAGE_ENCRYPTION_KEY', '')
    if not raw:
        try:
            from flask import current_app
            raw = current_app.config.get('MESSAGE_ENCRYPTION_KEY', '')
        except Exception:
            raw = ''
    if raw:
        try:
            _KEY = Fernet(raw.encode() if isinstance(raw, str) else raw)
            _HAS_KEY = True
            return _KEY
        except Exception:
            pass
    _HAS_KEY = False
    return None


def encrypt_message(plaintext):
    if not plaintext:
        return plaintext
    key = _get_key()
    if key is None:
        return plaintext
    if isinstance(plaintext, str):
        plaintext = plaintext.encode('utf-8')
    token = key.encrypt(plaintext)
    return ENC_PREFIX + token.decode()


def decrypt_message(ciphertext):
    if not ciphertext or not ciphertext.startswith(ENC_PREFIX):
        return ciphertext
    key = _get_key()
    if key is None:
        return ciphertext
    raw = ciphertext[len(ENC_PREFIX):].encode()
    return key.decrypt(raw).decode('utf-8')
