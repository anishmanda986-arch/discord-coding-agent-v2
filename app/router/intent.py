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
        r"^what is (react|python|javascript|typescript|vue|angular|docker|git|sql|rust|go|c\+\+|html|css|recursion|an algorithm|a database)\b",
        r"^explain (recursion|closure|async|await|event loop|pointers|interfaces|promises|rest|graphql|jwt|oauth|solid principles|design patterns)\b",
        r"^why is (python|javascript|rust|go|c|c\+\+|java) (slow|fast|popular|used|better|worse)\b",
        r"^which (language|framework|library|database|tool) (should i learn|is better|is best)\b",
        r"^difference between \w+ and \w+\b",
        r"^(can you help me|help me understand|what do you think of|tell me a joke)\b",
    ]

    # Explicit coding action keywords and indicators
    CODING_PATTERNS = [
        r"\b(build|create|implement|scaffold|code|develop|generate|write)\b.*?\b(app|application|website|api|bot|service|dashboard|component|script|microservice|frontend|backend|server|ui|page|module|program|handler|parser)\b",
        r"\b(fix|debug|resolve|repair|patch)\b.*?\b(error|bug|issue|failure|exception|crash|traceback|syntax error|type error|null pointer|404|500|broken)\b",
        r"\b(modify|edit|update|refactor|rewrite|optimize|change|add|remove|delete)\b.*?\b(function|class|method|file|code|component|endpoint|route|schema|dependency|package)\b",
        r"\b(add|implement|write)\b.*?\b(authentication|auth|login|signup|oauth|jwt|stripe|payment|database|table|migration|crud|pagination|websocket|caching|docker|dockerfile)\b",
        r"\b(run|execute|write|create|add)\b.*?\b(tests?|unit tests?|integration tests?|pytest|npm test|jest|unittest|build|linter|lint)\b",
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

        # Rule 1: Code blocks, stack traces, file extensions -> 100% CODING
        for pattern in self.CODING_PATTERNS:
            if re.search(pattern, clean, re.IGNORECASE):
                intent_res = (self.INTENT_CODING, 0.98, f"Matched coding trigger pattern: {pattern}")
                self._cache[key] = {"intent": intent_res[0], "confidence": intent_res[1], "reason": intent_res[2], "timestamp": time.time()}
                return intent_res

        # Rule 2: Pure conversational matches -> 100% CONVERSATION
        for pattern in self.CONVERSATIONAL_PATTERNS:
            if re.search(pattern, lower, re.IGNORECASE):
                intent_res = (self.INTENT_CONVERSATION, 0.95, f"Matched conversational trigger pattern: {pattern}")
                self._cache[key] = {"intent": intent_res[0], "confidence": intent_res[1], "reason": intent_res[2], "timestamp": time.time()}
                return intent_res

        # Rule 3: Short greetings / remarks (1-3 words) without coding verbs
        words = lower.split()
        if len(words) <= 3:
            common_chat_words = {"hello", "hi", "hey", "sup", "yo", "thanks", "thx", "cool", "nice", "ok", "okay", "bye", "good", "great", "awesome", "help", "who", "what"}
            if any(w in common_chat_words for w in words):
                intent_res = (self.INTENT_CONVERSATION, 0.90, "Short conversational phrase")
                self._cache[key] = {"intent": intent_res[0], "confidence": intent_res[1], "reason": intent_res[2], "timestamp": time.time()}
                return intent_res

        # Rule 4: Questions starting with "what", "why", "how", "when", "who", "where", "can you explain" without file or code creation verbs
        question_starters = ("what is", "what are", "why does", "why is", "why do", "how does", "how do", "can you explain", "explain to me", "what does")
        coding_actions = ("create", "build", "make a", "write a", "modify", "edit", "fix", "debug", "refactor", "generate a", "scaffold")
        if any(lower.startswith(q) for q in question_starters) and not any(action in lower for action in coding_actions):
            intent_res = (self.INTENT_CONVERSATION, 0.88, "Conceptual or informational question")
            self._cache[key] = {"intent": intent_res[0], "confidence": intent_res[1], "reason": intent_res[2], "timestamp": time.time()}
            return intent_res

        # Rule 5: Default action verbs check
        if any(action in lower for action in coding_actions):
            intent_res = (self.INTENT_CODING, 0.85, "Detected actionable coding directive")
            self._cache[key] = {"intent": intent_res[0], "confidence": intent_res[1], "reason": intent_res[2], "timestamp": time.time()}
            return intent_res

        # If ambiguous, default to CONVERSATION to prevent accidental expensive workspace creation
        intent_res = (self.INTENT_CONVERSATION, 0.70, "Defaulted to conversational to prevent unwanted workspace scaffolding")
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
