import unittest
from app.api_client.normalizer import ApiUrlNormalizer

class TestUrlNormalizer(unittest.TestCase):
    def test_clean_base_url_strips_trailing_slashes(self):
        url = "https://openrouter.ai/api/v1/"
        self.assertEqual(ApiUrlNormalizer.clean_base_url(url), "https://openrouter.ai/api/v1")

    def test_clean_base_url_removes_accidental_endpoints(self):
        url1 = "https://api.openai.com/v1/chat/completions"
        self.assertEqual(ApiUrlNormalizer.clean_base_url(url1), "https://api.openai.com/v1")

        url2 = "http://localhost:11434/v1/models"
        self.assertEqual(ApiUrlNormalizer.clean_base_url(url2), "http://localhost:11434/v1")

    def test_prevents_duplicated_v1_and_models(self):
        base = "https://integrate.api.nvidia.com/v1"
        models_url = ApiUrlNormalizer.get_models_url(base)
        self.assertEqual(models_url, "https://integrate.api.nvidia.com/v1/models")
        self.assertNotIn("/v1/v1", models_url)
        self.assertNotIn("/models/models", models_url)

        chat_url = ApiUrlNormalizer.get_chat_completions_url(base)
        self.assertEqual(chat_url, "https://integrate.api.nvidia.com/v1/chat/completions")
        self.assertNotIn("/chat/completions/chat/completions", chat_url)

    def test_sanitize_headers_adds_bearer(self):
        headers = ApiUrlNormalizer.sanitize_headers("my-secret-key")
        self.assertEqual(headers["Authorization"], "Bearer my-secret-key")
        self.assertEqual(headers["Content-Type"], "application/json")

if __name__ == "__main__":
    unittest.main()
