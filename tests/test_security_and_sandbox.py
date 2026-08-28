import unittest
import tempfile
import os
from pathlib import Path
from app.security.validator import SecurityValidator
from app.security.redaction import SecretRedactor
from app.security.crypto import CryptoManager

class TestSecurityAndSandbox(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.crypto = CryptoManager("test-secret-key-32-chars-long!")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_path_traversal_prevention(self):
        # Valid path
        valid, resolved, err = SecurityValidator.validate_workspace_path(self.tmp_dir, "src/index.ts")
        self.assertTrue(valid)
        self.assertIsNotNone(resolved)

        # Invalid path traversal attempts
        invalid1, _, _ = SecurityValidator.validate_workspace_path(self.tmp_dir, "../../etc/passwd")
        self.assertFalse(invalid1)

        invalid2, _, _ = SecurityValidator.validate_workspace_path(self.tmp_dir, "foo/bar/../../../root")
        self.assertFalse(invalid2)

    def test_command_safety_checks(self):
        safe_cmd = "pytest tests/ -v"
        is_safe, err = SecurityValidator.is_safe_command(safe_cmd)
        self.assertTrue(is_safe)
        self.assertIsNone(err)

        dangerous_cmd = "rm -rf / --no-preserve-root"
        is_safe2, err2 = SecurityValidator.is_safe_command(dangerous_cmd)
        self.assertFalse(is_safe2)

    def test_secret_redaction(self):
        text_with_key = "Error contacting OpenAI with key [REDACTED]"
        redacted = SecretRedactor.redact_text(text_with_key)
        self.assertNotIn("sk-abcdef", redacted)
        self.assertIn("[REDACTED_API_KEY]", redacted)

        discord_token = "[DISCORD_TOKEN]"
        redacted_discord = SecretRedactor.redact_text(f"Bot token: {discord_token}")
        self.assertNotIn(discord_token, redacted_discord)
        self.assertIn("[REDACTED_DISCORD_TOKEN]", redacted_discord)

    def test_encryption_roundtrip(self):
        secret = "[API_KEY]"
        encrypted = self.crypto.encrypt_secret(secret)
        self.assertNotEqual(secret, encrypted)
        decrypted = self.crypto.decrypt_secret(encrypted)
        self.assertEqual(secret, decrypted)

    def test_hmac_signing_and_verification(self):
        msg = "agent_connect_payload"
        sig = self.crypto.sign_message(msg)
        self.assertTrue(self.crypto.verify_signature(msg, sig))
        self.assertFalse(self.crypto.verify_signature("tampered_payload", sig))

if __name__ == "__main__":
    unittest.main()
