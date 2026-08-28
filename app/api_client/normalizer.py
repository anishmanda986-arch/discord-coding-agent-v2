import re
from urllib.parse import urlparse, urlunparse

class ApiUrlNormalizer:
    """
    Normalizes OpenAI-compatible base URLs and ensures clean endpoint derivation.
    Prevents common bugs such as:
      - /v1/v1/models
      - /models/models
      - /chat/completions/chat/completions
      - double slashes in paths
      - improper scheme/host parsing
    """

    @classmethod
    def clean_base_url(cls, raw_url: str) -> str:
        """
        Cleans and standardizes the base URL.
        Example inputs -> outputs:
          - "https://openrouter.ai/api/v1/" -> "https://openrouter.ai/api/v1"
          - "https://api.openai.com/v1/chat/completions" -> "https://api.openai.com/v1"
          - "http://localhost:11434/v1/models" -> "http://localhost:11434/v1"
          - "https://integrate.api.nvidia.com/v1/" -> "https://integrate.api.nvidia.com/v1"
        """
        if not raw_url or not isinstance(raw_url, str):
            return "https://openrouter.ai/api/v1"
            
        url = raw_url.strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
            
        parsed = urlparse(url)
        path = parsed.path
        
        # Remove trailing slash
        path = path.rstrip("/")
        
        # Remove duplicated endpoints accidentally pasted by users
        path = re.sub(r"/chat/completions/?$", "", path, flags=re.IGNORECASE)
        path = re.sub(r"/models/?$", "", path, flags=re.IGNORECASE)
        path = re.sub(r"/embeddings/?$", "", path, flags=re.IGNORECASE)
        
        # Collapse multiple slashes (except protocol)
        path = re.sub(r"/{2,}", "/", path)
        
        # Reconstruct
        clean_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            path,
            "", "", ""
        )).rstrip("/")
        
        return clean_url

    @classmethod
    def get_models_url(cls, base_url: str) -> str:
        """
        Derives the GET /models endpoint correctly.
        """
        clean_base = cls.clean_base_url(base_url)
        # Ensure we don't end up with /models/models
        if clean_base.endswith("/models"):
            return clean_base
        return f"{clean_base}/models"

    @classmethod
    def get_chat_completions_url(cls, base_url: str) -> str:
        """
        Derives the POST /chat/completions endpoint correctly.
        """
        clean_base = cls.clean_base_url(base_url)
        if clean_base.endswith("/chat/completions"):
            return clean_base
        return f"{clean_base}/chat/completions"

    @classmethod
    def sanitize_headers(cls, api_key: str, extra_headers: dict = None) -> dict:
        """
        Constructs standard Authorization and platform headers.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key.strip() if api_key else ''}",
            "HTTP-Referer": "https://discord.com",
            "X-Title": "Coding Agent",
        }
        if extra_headers:
            headers.update(extra_headers)
        return headers
