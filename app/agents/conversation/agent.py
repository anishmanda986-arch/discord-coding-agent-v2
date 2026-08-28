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
        if any(w in lower for w in ("hello", "hi", "hey", "good morning", "good evening")):
            reply = "Hello! 👋 I'm your Discord Coding Agent. I can chat about programming concepts, explain architectures, or autonomously build and fix projects when you give me a coding task."
        elif "what is react" in lower:
            reply = "React is a popular open-source JavaScript library developed by Meta for building user interfaces, especially single-page applications (SPAs). It uses a declarative component-based model, Virtual DOM, and state hooks like `useState` and `useEffect` to efficiently render dynamic web UIs."
        elif "what can you do" in lower or "who are you" in lower:
            reply = "I'm an autonomous Discord Coding Agent! Here's what I can do:\n- 💬 **Chat & Explain**: Answer technical questions, debug advice, and architectural discussions.\n- 🛠️ **Autonomous Coding**: Build, refactor, debug, test, and package complete projects from prompts.\n- ⚙️ **Slash Commands**: `/api` (configure models), `/test` (system diagnostics), `/connect` (gateway), `/disable` (channel isolation)."
        elif "explain recursion" in lower:
            reply = "Recursion is a programming technique where a function calls itself to solve a smaller instance of the same problem until it reaches a base condition.\n\nExample in Python:\n```python\ndef factorial(n):\n    if n <= 1:  # Base case\n        return 1\n    return n * factorial(n - 1)  # Recursive case\n```"
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
