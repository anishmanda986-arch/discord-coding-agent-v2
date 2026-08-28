import time
from typing import Dict, Any, Optional
from ..base import BaseAgent
from ...router.router import AgentMessage
from ...api_client.client import OpenAICompatibleClient
from ...security.redaction import SecretRedactor

class ConversationAgent(BaseAgent):
    """
    Lightweight Conversational Assistant Agent.
    Handles normal Discord messages (greetings, explanations, technical questions, discussions).
    Operates strictly in-memory:
      - Does NOT create workspaces or write files.
      - Does NOT run coding tools or sandbox commands.
      - Does NOT create ZIP archives or status progress loops.
      - Consumes minimal tokens and returns fast markdown answers.
    """

    DEFAULT_SYSTEM_PROMPT = """You are a helpful, knowledgeable AI assistant and Discord coding companion.
You provide clear, friendly, and concise responses to questions, explanations, discussions, and concepts.
When explaining technical concepts, use clear formatting, concise code snippets where helpful, and straightforward explanations.
Keep your responses engaging, helpful, and formatted nicely in Discord-compatible Markdown.
"""

    def __init__(self):
        super().__init__(name="conversation_agent", role="Conversational AI Assistant")

    async def generate_response(
        self,
        prompt: str,
        client: Optional[OpenAICompatibleClient] = None,
        model: str = "google/gemini-2.5-flash",
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates a direct conversational response to the user's prompt.
        """
        start_time = time.time()
        
        # If client is provided, call OpenAI-compatible API
        if client:
            messages = [
                {"role": "system", "content": system_prompt or self.DEFAULT_SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            resp = await client.chat_completion(
                messages=messages,
                model=model,
                temperature=0.7,
                max_tokens=2048
            )
            content = resp.get("content") or "Hello! I am your AI assistant. How can I help you today?"
            usage = resp.get("usage", {})
            return {
                "success": True,
                "type": "conversation",
                "content": SecretRedactor.redact_text(content),
                "model": resp.get("model", model),
                "usage": usage,
                "elapsed_seconds": round(time.time() - start_time, 3)
            }

        # Fallback offline conversational heuristic responses for common greetings / questions
        lower = prompt.lower().strip()
        if any(w in lower for w in ("hello", "hi", "hey", "good morning", "good evening", "namaste", "kem cho")):
            reply = "Hello! 👋 I'm your Discord Coding Agent. I can chat, explain architectures, discuss debugging strategies, or autonomously build, test, and package complete projects when you provide a coding request."
        elif "what is react" in lower:
            reply = "React is a popular open-source JavaScript library developed by Meta for building user interfaces, especially single-page applications (SPAs). It uses a declarative component-based model, Virtual DOM, and state hooks like `useState` and `useEffect` to efficiently render dynamic web UIs."
        elif "what can you do" in lower or "who are you" in lower:
            reply = "I'm an autonomous Discord Coding Agent! Here is what I do:\n- 💬 **Normal Conversation**: Chat about tech, architecture, debugging advice, or answer programming questions.\n- 🛠️ **Autonomous Coding**: Build, refactor, debug, test, and package complete projects into downloadable ZIP archives.\n- ⚙️ **Slash Commands**:\n  • `/api` — Configure providers (OpenRouter/OpenAI/Ollama) & encrypt API keys.\n  • `/models` — Discover and filter available LLM models.\n  • `/token` (`--admin`) — Inspect token quotas, cache savings, and cost breakdowns.\n  • `/switch` — Switch active models or toggle automated fallback.\n  • `/test` — Run 21-point system diagnostics or sandbox project test suites.\n  • `/connect` — HMAC gateway registration for worker agents.\n  • `/disable` — Isolate/toggle bot activity in specific channels."
        elif any(c in lower for c in ("/token", "/switch", "/test", "/models", "/api", "command")):
            reply = "Here are the supported bot commands:\n- `/models [query]` — View and filter models from the active provider.\n- `/token [--admin]` — Check token usage, cache savings, and quota limits.\n- `/switch [model_name] [auto: on/off]` — Change active LLM or enable automatic fallback.\n- `/test` — Run 21-point system diagnostics or project test suites.\n- `/api [provider] [base_url] [key]` — Configure custom OpenAI-compatible endpoint.\n- `/disable` — Mute or unmute the bot in the current channel."
        elif "explain recursion" in lower:
            reply = "Recursion is a programming technique where a function calls itself to solve a smaller instance of the same problem until it reaches a base condition.\n\nExample in Python:\n```python\ndef factorial(n):\n    if n <= 1:  # Base case\n        return 1\n    return n * factorial(n - 1)  # Recursive case\n```"
        elif any(k in lower for k in ("kya", "kaise", "bhai", "yaar", "batao", "kuch")):
            reply = "Haan bhai! Main ready hoon. Agar aapko normal chat/discussion karni hai ya kisi programming concept ko samajhna hai to batao. Agar koi project ya code banwana hai (jaise 'build a react app' ya 'fix login error'), to prompt do — main autonomously code likh kar, test run karke deliverable provide kar dunga."
        else:
            reply = f"Thank you for your message! If you have a question or want to discuss programming concepts, let me know. To start an autonomous coding task, give me a prompt like `build a React weather app` or `fix the login error`."

        return {
            "success": True,
            "type": "conversation",
            "content": reply,
            "model": "offline-conversational-agent",
            "usage": {"prompt_tokens": len(prompt)//4, "completion_tokens": len(reply)//4, "total_tokens": (len(prompt)+len(reply))//4},
            "elapsed_seconds": round(time.time() - start_time, 3)
        }

    async def handle_message(self, message: AgentMessage) -> AgentMessage:
        payload = message.payload
        prompt = payload.get("prompt", "")
        model = payload.get("model", "google/gemini-2.5-flash")
        res = await self.generate_response(prompt=prompt, model=model)
        return self.create_result_message(message, res)
