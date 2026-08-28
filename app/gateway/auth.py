import time
import hmac
import hashlib
from typing import Tuple, Optional
from ..security.crypto import CryptoManager

class GatewayAuthenticator:
    """
    Validates gateway requests using HMAC authentication and timestamp-based replay protection.
    """

    def __init__(self, shared_secret: str = "default-gateway-secret-32-chars!"):
        self.crypto = CryptoManager(shared_secret)

    def generate_auth_header(self, payload_body: str) -> str:
        timestamp = str(int(time.time()))
        message = f"{timestamp}:{payload_body}"
        signature = self.crypto.sign_message(message)
        return f"t={timestamp},v1={signature}"

    def verify_request(self, auth_header: Optional[str], payload_body: str, max_age_seconds: int = 300) -> Tuple[bool, Optional[str]]:
        if not auth_header:
            return False, "Missing Authorization header."

        try:
            parts = dict(item.split("=", 1) for item in auth_header.split(","))
            timestamp_str = parts.get("t")
            signature = parts.get("v1")

            if not timestamp_str or not signature:
                return False, "Malformed Authorization header format (expected t=...,v1=...)."

            req_time = int(timestamp_str)
            now = int(time.time())

            if abs(now - req_time) > max_age_seconds:
                return False, "Request expired (timestamp out of tolerance window)."

            message = f"{timestamp_str}:{payload_body}"
            if not self.crypto.verify_signature(message, signature):
                return False, "Invalid signature: authentication failed."

            return True, None
        except Exception as e:
            return False, f"Auth verification error: {str(e)}"

    def verify_auth_header(self, auth_header: Optional[str], payload_body: str, max_age_seconds: int = 300) -> bool:
        """Convenience wrapper returning boolean whether request auth is valid."""
        ok, _ = self.verify_request(auth_header, payload_body, max_age_seconds)
        return ok
