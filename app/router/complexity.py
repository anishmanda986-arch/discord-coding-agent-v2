import re
from typing import Dict, Any, Tuple

class TaskComplexityRouter:
    """
    Classifies task complexity to select optimal model and token budget:
      - TRIVIAL: typos, simple config changes, single word/line edits
      - SMALL: 1 file fix, helper function, simple test addition
      - MEDIUM: feature in 2-4 related files, API route + service
      - LARGE: full subsystem, frontend + backend integration
      - COMPLEX: multi-system architecture, full SaaS scaffold, major refactoring
    """

    COMPLEXITY_BUDGETS = {
        "TRIVIAL": {"max_tokens": 8000, "max_calls": 3, "model_type": "fast", "max_tools": 6},
        "SMALL": {"max_tokens": 20000, "max_calls": 6, "model_type": "fast", "max_tools": 12},
        "MEDIUM": {"max_tokens": 50000, "max_calls": 12, "model_type": "strong", "max_tools": 20},
        "LARGE": {"max_tokens": 90000, "max_calls": 20, "model_type": "strong", "max_tools": 30},
        "COMPLEX": {"max_tokens": 150000, "max_calls": 25, "model_type": "strong", "max_tools": 40},
    }

    @classmethod
    def classify_prompt(cls, prompt: str, repo_file_count: int = 0) -> Tuple[str, Dict[str, Any]]:
        prompt_lower = prompt.lower()
        word_count = len(prompt.split())

        # Heuristic triggers
        is_complex = any(k in prompt_lower for k in (
            "from scratch", "full stack", "fullstack", "saas", "dashboard", "microservice",
            "refactor entire", "architecture", "multi-tenant", "authentication system", "complete app"
        ))
        is_large = any(k in prompt_lower for k in (
            "implement feature", "integrate", "add endpoint and database", "redesign",
            "dockerize and test", "payment gateway", "crud"
        ))
        is_small = any(k in prompt_lower for k in (
            "fix typo", "fix bug in", "update function", "add test for", "rename variable", "fix lint"
        ))
        is_trivial = word_count <= 6 and any(k in prompt_lower for k in (
            "fix typo", "change version", "update color", "format", "fix syntax"
        ))

        if is_complex or (repo_file_count > 50 and is_large):
            complexity = "COMPLEX"
        elif is_large:
            complexity = "LARGE"
        elif is_trivial:
            complexity = "TRIVIAL"
        elif is_small or word_count < 12:
            complexity = "SMALL"
        else:
            complexity = "MEDIUM"

        budget = cls.COMPLEXITY_BUDGETS[complexity]
        return complexity, budget
