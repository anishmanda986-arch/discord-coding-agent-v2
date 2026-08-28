import re
import time
from typing import Dict, Any, Tuple, Optional
from ..security.redaction import SecretRedactor

class IntentRouter:
    """
    Intelligent Intent Classifier:
    Separates NORMAL CONVERSATION from AUTONOMOUS CODING REQUESTS.
    
    1. Heuristic Rule-Based Classifier (Instant, 0 tokens)
    2. In-memory LRU/TTL Intent Cache
    3. Cheap LLM Intent Classifier (Fallback only when truly ambiguous)
    """

    INTENT_CONVERSATION = "CONVERSATION"
    INTENT_CODING = "CODING"

    # Conversational keywords and patterns
    CONVERSATIONAL_PATTERNS = [
        r"^(hi|hello|hey|greetings|howdy|yo|good morning|good afternoon|good evening)\b",
        r"^how are you",
        r"^what can you do",
        r"^who are you",
        r"^tell me about yourself",
        r"^thank(s| you)?\b",
        r"^bye|goodbye|see ya",
        r"^(kya|kaise|kuch|bhai|batao|sun|yaar|kya haal|namaste|kem cho|kya chal raha)\b",
        r"^(what is|what are|what do you mean by|tell me about)\b",
        r"^(explain|describe|clarify|teach me)\b",
        r"^(why is|why are|why do|why does)\b",
        r"^(which is better|which one should i|what should i use)\b",
        r"^(difference between|compare)\b",
        r"^(can you help me|help me understand|what do you think of|tell me a joke)\b",
    ]

    # Explicit coding action keywords and indicators (must be genuine directives)
    CODING_PATTERNS = [
        r"\b(build|create|implement|scaffold|develop|generate)\b.*?\b(app|application|website|api|bot|service|dashboard|component|microservice|frontend|backend|server|ui|page|module|program|system)\b",
        r"\b(fix|debug|resolve|repair|patch)\b.*?\b(error|bug|issue|failure|exception|crash|traceback|syntax error|type error|null pointer|404|500|broken)\b",
        r"\b(refactor|rewrite|optimize|change|add endpoint|add route|add migration|add feature)\b",
        r"\b(add|implement|write)\b.*?\b(authentication|auth|login|signup|oauth|jwt|stripe|payment|database|table|migration|crud|pagination|websocket|dockerfile)\b",
        r"\b(run tests?|pytest|npm test|jest|cargo test|go test)\b",
        r"\b(\.py|\.ts|\.tsx|\.js|\.jsx|\.json|\.html|\.css|\.sql|\.go|\.rs|\.java|\.cpp|\.c|\.sh|\.yml|\.yaml|package\.json|tsconfig\.json|Dockerfile)\b",
        r"```[a-zA-Z]*\n",
        r"Traceback \(most recent call last\):",
        r"Error: Cannot find module",
        r"TypeError:",
        r"SyntaxError:",
        r"ReferenceError:",
        r"NullPointerException",
    ]

    def __init__(self, cache_ttl_seconds: int = 3600):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = cache_ttl_seconds

    def _normalize_key(self, prompt: str) -> str:
        return prompt.strip().lower()

    def classify_intent_fast(self, prompt: str) -> Tuple[str, float, str]:
        """
        Fast rule-based intent classification.
        Returns: (intent, confidence, reason)
        """
        clean = prompt.strip()
        lower = clean.lower()

        # Check cache
        key = self._normalize_key(prompt)
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry["timestamp"] < self.cache_ttl:
                return entry["intent"], entry["confidence"], entry["reason"]

        # Rule 1: Code blocks, stack traces, explicit code errors -> 100% CODING
        code_block_patterns = [
            r"```[a-zA-Z]*\n",
            r"Traceback \(most recent call last\):",
            r"Error: Cannot find module",
            r"TypeError:",
            r"SyntaxError:",
            r"ReferenceError:",
            r"NullPointerException"
        ]
        for pattern in code_block_patterns:
            if re.search(pattern, clean, re.IGNORECASE):
                intent_res = (self.INTENT_CODING, 0.98, f"Matched raw error/code block pattern: {pattern}")
                self._cache[key] = {"intent": intent_res[0], "confidence": intent_res[1], "reason": intent_res[2], "timestamp": time.time()}
                return intent_res

        # Rule 2: Pure conversational matches & questions -> 100% CONVERSATION
        for pattern in self.CONVERSATIONAL_PATTERNS:
            if re.search(pattern, lower, re.IGNORECASE):
                intent_res = (self.INTENT_CONVERSATION, 0.95, f"Matched conversational trigger pattern: {pattern}")
                self._cache[key] = {"intent": intent_res[0], "confidence": intent_res[1], "reason": intent_res[2], "timestamp": time.time()}
                return intent_res

        # Rule 3: Short greetings / remarks / complaints / Hindi-English conversational phrases
        words = lower.split()
        if len(words) <= 5:
            common_chat_words = {"hello", "hi", "hey", "sup", "yo", "thanks", "thx", "cool", "nice", "ok", "okay", "bye", "good", "great", "awesome", "help", "who", "what", "kya", "bhai", "yaar", "kaise", "test", "check"}
            if any(w in common_chat_words for w in words) and not any(w in ("build", "create", "scaffold", "fix", "debug", "refactor") for w in words):
                intent_res = (self.INTENT_CONVERSATION, 0.90, "Short conversational phrase")
                self._cache[key] = {"intent": intent_res[0], "confidence": intent_res[1], "reason": intent_res[2], "timestamp": time.time()}
                return intent_res

        # Rule 4: Questions starting with "what", "why", "how", "when", "who", "where", "can you explain", "kya"
        question_starters = ("what is", "what are", "why does", "why is", "why do", "how does", "how do", "can you explain", "explain to me", "what does", "kya", "kaise", "batao")
        coding_actions = ("build an app", "create an app", "make an app", "write an app", "implement an app", "scaffold", "fix the bug", "debug this error", "refactor this code")
        if any(lower.startswith(q) for q in question_starters) and not any(action in lower for action in coding_actions):
            intent_res = (self.INTENT_CONVERSATION, 0.92, "Conceptual or informational question")
            self._cache[key] = {"intent": intent_res[0], "confidence": intent_res[1], "reason": intent_res[2], "timestamp": time.time()}
            return intent_res

        # Rule 5: Explicit action coding patterns check
        for pattern in self.CODING_PATTERNS:
            if re.search(pattern, clean, re.IGNORECASE):
                intent_res = (self.INTENT_CODING, 0.92, f"Matched actionable coding trigger: {pattern}")
                self._cache[key] = {"intent": intent_res[0], "confidence": intent_res[1], "reason": intent_res[2], "timestamp": time.time()}
                return intent_res

        # Default safely to CONVERSATION
        intent_res = (self.INTENT_CONVERSATION, 0.80, "Defaulted to conversational to prevent unwanted workspace scaffolding")
        self._cache[key] = {"intent": intent_res[0], "confidence": intent_res[1], "reason": intent_res[2], "timestamp": time.time()}
        return intent_res

    def classify_intent_heuristic(self, prompt: str) -> str:
        """Convenience method returning string intent ('CONVERSATION' or 'CODING')."""
        intent, _, _ = self.classify_intent_fast(prompt)
        return intent

    def classify_intent(self, prompt: str) -> str:
        """Alias for classify_intent_heuristic."""
        return self.classify_intent_heuristic(prompt)

    async def classify_intent_with_model(self, prompt: str, client: Optional[Any] = None, fast_model: str = "google/gemini-2.5-flash") -> str:
        """
        Uses rule heuristics first. If confidence >= 0.85, skips LLM call entirely.
        Otherwise calls cheap/fast model for intent classification.
        """
        intent, confidence, reason = self.classify_intent_fast(prompt)
        if confidence >= 0.85 or not client:
            return intent

        # Cheap classification prompt
        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an intent classifier for a Discord assistant. "
                        "Determine if the user's message is a NORMAL_CHAT (greeting, explanation, concept question, chat) "
                        "or a CODING_REQUEST (request to build, modify, fix, debug, write code, run tests, or edit files). "
                        "Respond with ONLY one word: 'CONVERSATION' or 'CODING'."
                    )
                },
                {"role": "user", "content": prompt}
            ]
            resp = await client.chat_completion(
                messages=messages,
                model=fast_model,
                temperature=0.0,
                max_tokens=10
            )
            content = (resp.get("content") or "").strip().upper()
            if "CODING" in content:
                final_intent = self.INTENT_CODING
            else:
                final_intent = self.INTENT_CONVERSATION

            key = self._normalize_key(prompt)
            self._cache[key] = {"intent": final_intent, "confidence": 0.99, "reason": "LLM classified", "timestamp": time.time()}
            return final_intent
        except Exception:
            return intent
