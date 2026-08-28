import time
import json
import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator, Tuple
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from .normalizer import ApiUrlNormalizer
from ..security.redaction import SecretRedactor

class OpenAICompatibleClient:
    """
    Production-grade OpenAI-compatible API client.
    Features:
      - Exponential backoff retry for 429, 502, 503, timeouts (1s, 2s, 4s, 8s)
      - Respects Retry-After headers
      - Token usage extraction (prompt_tokens, completion_tokens, total_tokens)
      - Strict secret redaction in all exception messages
      - Model timeout and cancellation handling
    """

    RETRY_BACKOFF = [1.0, 2.0, 4.0, 8.0]
    RETRYABLE_STATUSES = {429, 500, 502, 503, 504}

    def __init__(self, base_url: str, api_key: str, default_model: str = "gpt-4o"):
        self.base_url = ApiUrlNormalizer.clean_base_url(base_url)
        self.api_key = api_key
        self.default_model = default_model

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = 4096,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        response_format: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Executes a robust completion with retry logic.
        Returns dict with:
          {
            "content": str,
            "tool_calls": list,
            "usage": {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int},
            "model": str,
            "finish_reason": str
          }
        """
        target_model = model or self.default_model
        chat_url = ApiUrlNormalizer.get_chat_completions_url(self.base_url)
        headers = ApiUrlNormalizer.sanitize_headers(self.api_key)

        payload: Dict[str, Any] = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if tools:
            payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice
        if response_format:
            payload["response_format"] = response_format

        data_bytes = json.dumps(payload).encode("utf-8")
        last_error = None

        for attempt, backoff in enumerate(self.RETRY_BACKOFF):
            try:
                loop = asyncio.get_event_loop()
                
                def _do_request():
                    req = Request(chat_url, data=data_bytes, headers=headers, method="POST")
                    with urlopen(req, timeout=60) as res:
                        return json.loads(res.read().decode("utf-8"))

                resp_json = await loop.run_in_executor(None, _do_request)
                
                # Parse response
                choice = resp_json.get("choices", [{}])[0]
                message = choice.get("message", {})
                content = message.get("content") or ""
                tool_calls = message.get("tool_calls", [])
                finish_reason = choice.get("finish_reason", "stop")
                usage = resp_json.get("usage", {
                    "prompt_tokens": len(str(messages)) // 4,
                    "completion_tokens": len(content) // 4,
                    "total_tokens": (len(str(messages)) + len(content)) // 4
                })

                return {
                    "content": content,
                    "tool_calls": tool_calls,
                    "usage": usage,
                    "model": resp_json.get("model", target_model),
                    "finish_reason": finish_reason,
                    "error": None
                }

            except HTTPError as e:
                status = e.code
                headers_dict = dict(e.headers.items()) if hasattr(e, "headers") else {}
                retry_after_hdr = headers_dict.get("Retry-After") or headers_dict.get("retry-after")
                
                if status in self.RETRYABLE_STATUSES and attempt < len(self.RETRY_BACKOFF) - 1:
                    sleep_time = float(retry_after_hdr) if retry_after_hdr and retry_after_hdr.isdigit() else backoff
                    await asyncio.sleep(sleep_time)
                    continue
                else:
                    # Non-retryable or max retries exceeded
                    try:
                        err_body = e.read().decode("utf-8")
                    except Exception:
                        err_body = str(e.reason)
                    clean_err = SecretRedactor.redact_text(f"API Error {status}: {err_body}")
                    return {
                        "content": "",
                        "tool_calls": [],
                        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                        "model": target_model,
                        "finish_reason": "error",
                        "error": clean_err
                    }

            except Exception as e:
                last_error = SecretRedactor.redact_text(str(e))
                if attempt < len(self.RETRY_BACKOFF) - 1:
                    await asyncio.sleep(backoff)
                    continue

        return {
            "content": "",
            "tool_calls": [],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "model": target_model,
            "finish_reason": "error",
            "error": f"API request failed after {len(self.RETRY_BACKOFF)} attempts: {last_error}"
        }
