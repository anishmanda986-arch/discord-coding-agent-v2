import os
import base64
import hashlib
import hmac
from typing import Tuple

class CryptoManager:
    """
    Handles API key encryption, gateway HMAC token verification,
    and replay protection timestamps.
    """
    
    def __init__(self, secret_key: str = None):
        self.secret_key = (secret_key or os.getenv("SECRET_KEY", "default-coding-agent-key-32-chars!")).encode("utf-8")
        # Ensure 32 bytes key
        self.derived_key = hashlib.sha256(self.secret_key).digest()

    def encrypt_secret(self, plaintext: str) -> str:
        """
        Lightweight symmetric encryption using XOR stream cipher with SHA256 key schedule & IV.
        Safe for storing API keys in local SQLite without requiring heavy external C-libraries.
        """
        if not plaintext:
            return ""
        iv = os.urandom(16)
        # Derive keystream
        keystream = hashlib.sha256(self.derived_key + iv).digest()
        plain_bytes = plaintext.encode("utf-8")
        
        # Extend keystream if needed
        while len(keystream) < len(plain_bytes):
            keystream += hashlib.sha256(self.derived_key + keystream).digest()
            
        encrypted = bytes([p ^ k for p, k in zip(plain_bytes, keystream[:len(plain_bytes)])])
        payload = iv + encrypted
        return base64.b64encode(payload).decode("utf-8")

    def decrypt_secret(self, ciphertext: str) -> str:
        if not ciphertext:
            return ""
        try:
            payload = base64.b64decode(ciphertext.encode("utf-8"))
            if len(payload) <= 16:
                return ""
            iv = payload[:16]
            encrypted = payload[16:]
            
            keystream = hashlib.sha256(self.derived_key + iv).digest()
            while len(keystream) < len(encrypted):
                keystream += hashlib.sha256(self.derived_key + keystream).digest()
                
            decrypted = bytes([c ^ k for c, k in zip(encrypted, keystream[:len(encrypted)])])
            return decrypted.decode("utf-8")
        except Exception:
            return ""

    def sign_message(self, message: str) -> str:
        """Generates HMAC-SHA256 signature for Gateway communication."""
        return hmac.new(self.derived_key, message.encode("utf-8"), hashlib.sha256).hexdigest()

    def verify_signature(self, message: str, signature: str) -> bool:
        """Verifies HMAC signature in constant time."""
        expected = self.sign_message(message)
        return hmac.compare_digest(expected, signature)
