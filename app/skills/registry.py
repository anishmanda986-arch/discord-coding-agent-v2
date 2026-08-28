import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

class SkillRegistry:
    """
    Dynamic modular skill system for the Coding Agent.
    Matches task keywords and context to load ONLY relevant skills on-demand,
    saving tokens while supplying authoritative domain workflows and checklists.
    """

    SKILLS_METADATA = {
        "software-engineering": {
            "keywords": ["architecture", "clean code", "solid", "design pattern", "refactor", "software"],
            "title": "Software Engineering Principles",
            "file": "software-engineering/SKILL.md"
        },
        "web-development": {
            "keywords": ["web", "http", "rest", "html", "css", "browser", "spa"],
            "title": "Modern Web Development",
            "file": "web-development/SKILL.md"
        },
        "frontend": {
            "keywords": ["frontend", "ui", "component", "button", "layout", "view", "tailwind", "css"],
            "title": "Frontend Engineering",
            "file": "frontend/SKILL.md"
        },
        "backend": {
            "keywords": ["backend", "server", "api", "endpoint", "controller", "service", "middleware"],
            "title": "Backend Engineering",
            "file": "backend/SKILL.md"
        },
        "fullstack": {
            "keywords": ["fullstack", "full-stack", "dashboard", "saas", "client and server"],
            "title": "Fullstack Application Architecture",
            "file": "fullstack/SKILL.md"
        },
        "react": {
            "keywords": ["react", "jsx", "tsx", "usestate", "useeffect", "hook", "component"],
            "title": "React Component & State Architecture",
            "file": "react/SKILL.md"
        },
        "nextjs": {
            "keywords": ["nextjs", "next.js", "app router", "server component", "ssr", "getserversideprops"],
            "title": "Next.js Framework Master",
            "file": "nextjs/SKILL.md"
        },
        "typescript": {
            "keywords": ["typescript", "ts", "interface", "type", "generic", "tsconfig"],
            "title": "TypeScript Strict Typing",
            "file": "typescript/SKILL.md"
        },
        "javascript": {
            "keywords": ["javascript", "js", "es6", "node", "async/await", "promise"],
            "title": "Modern JavaScript ESNext",
            "file": "javascript/SKILL.md"
        },
        "python": {
            "keywords": ["python", "py", "fastapi", "flask", "django", "pydantic", "pip"],
            "title": "Python 3.12+ Async & Modern Architecture",
            "file": "python/SKILL.md"
        },
        "android": {
            "keywords": ["android", "apk", "gradle", "manifest", "activity", "intent"],
            "title": "Android Application Development",
            "file": "android/SKILL.md"
        },
        "kotlin": {
            "keywords": ["kotlin", "kt", "coroutine", "compose", "jetpack"],
            "title": "Kotlin & Jetpack Compose",
            "file": "kotlin/SKILL.md"
        },
        "discord": {
            "keywords": ["discord", "bot", "discord.py", "embed", "slash command", "interaction", "guild"],
            "title": "Discord Bot & Interaction Engineering",
            "file": "discord/SKILL.md"
        },
        "api-integration": {
            "keywords": ["api", "integration", "webhook", "rest", "fetch", "http client", "payload"],
            "title": "API Integration & Client Design",
            "file": "api-integration/SKILL.md"
        },
        "openrouter": {
            "keywords": ["openrouter", "openai-compatible", "nim", "model discovery", "ai endpoint"],
            "title": "OpenRouter & AI Gateway Integration",
            "file": "openrouter/SKILL.md"
        },
        "database": {
            "keywords": ["database", "db", "sql", "migration", "query", "orm", "schema"],
            "title": "Database Schema & Query Design",
            "file": "database/SKILL.md"
        },
        "postgresql": {
            "keywords": ["postgres", "postgresql", "pg", "psql", "relational"],
            "title": "PostgreSQL Optimization & Schemas",
            "file": "postgresql/SKILL.md"
        },
        "mongodb": {
            "keywords": ["mongo", "mongodb", "nosql", "document", "mongoose"],
            "title": "MongoDB Document Modeling",
            "file": "mongodb/SKILL.md"
        },
        "redis": {
            "keywords": ["redis", "cache", "pubsub", "session store", "key-value"],
            "title": "Redis In-Memory Caching & Queues",
            "file": "redis/SKILL.md"
        },
        "testing": {
            "keywords": ["test", "pytest", "jest", "unittest", "mock", "coverage", "tdd", "assert"],
            "title": "Automated Testing & QA",
            "file": "testing/SKILL.md"
        },
        "debugging": {
            "keywords": ["debug", "error", "stacktrace", "bug", "fix failure", "crash", "500"],
            "title": "Systematic Root-Cause Debugging",
            "file": "debugging/SKILL.md"
        },
        "security": {
            "keywords": ["security", "auth", "jwt", "sanitize", "secret", "injection", "xss", "csrf"],
            "title": "Application Security & Hardening",
            "file": "security/SKILL.md"
        },
        "docker": {
            "keywords": ["docker", "dockerfile", "container", "compose", "image"],
            "title": "Docker Containerization",
            "file": "docker/SKILL.md"
        },
        "devops": {
            "keywords": ["devops", "ci/cd", "pipeline", "deploy", "action", "kubernetes"],
            "title": "DevOps & Deployment Pipelines",
            "file": "devops/SKILL.md"
        },
        "github": {
            "keywords": ["github", "pr", "pull request", "issue", "clone", "repo"],
            "title": "GitHub Collaboration & Actions",
            "file": "github/SKILL.md"
        },
        "git": {
            "keywords": ["git", "commit", "branch", "merge", "rebase", "diff"],
            "title": "Git Workflow & Version Control",
            "file": "git/SKILL.md"
        },
        "ui-ux": {
            "keywords": ["ui", "ux", "design", "contrast", "spacing", "accessibility", "tailwind"],
            "title": "UI/UX & Visual Craftsmanship",
            "file": "ui-ux/SKILL.md"
        },
        "performance": {
            "keywords": ["performance", "latency", "optimize", "speed", "memory", "profiling"],
            "title": "Performance Optimization & Benchmarking",
            "file": "performance/SKILL.md"
        },
        "documentation": {
            "keywords": ["documentation", "readme", "docstring", "manual", "guide", "markdown"],
            "title": "Technical Documentation",
            "file": "documentation/SKILL.md"
        },
        "accessibility": {
            "keywords": ["accessibility", "a11y", "wcag", "screen reader", "keyboard navigation", "aria"],
            "title": "Accessibility & WCAG Engineering",
            "file": "accessibility/SKILL.md"
        },
    }

    def __init__(self, skills_dir: Optional[str] = None):
        if skills_dir:
            self.skills_dir = Path(skills_dir)
        else:
            self.skills_dir = Path(__file__).parent / "definitions"

    def match_relevant_skills(self, prompt: str, max_skills: int = 3) -> List[Dict[str, Any]]:
        prompt_lower = prompt.lower()
        matched = []

        for skill_id, meta in self.SKILLS_METADATA.items():
            score = 0
            for kw in meta["keywords"]:
                if re.search(r"\b" + re.escape(kw) + r"\b", prompt_lower):
                    score += 10
                elif kw in prompt_lower:
                    score += 4

            if score > 0:
                matched.append((score, skill_id, meta))

        matched.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, s_id, meta in matched[:max_skills]:
            results.append({
                "id": s_id,
                "title": meta["title"],
                "file": meta["file"],
                "score": score
            })

        # Default to software-engineering if none matched
        if not results:
            results.append({
                "id": "software-engineering",
                "title": self.SKILLS_METADATA["software-engineering"]["title"],
                "file": self.SKILLS_METADATA["software-engineering"]["file"],
                "score": 1
            })

        return results

    def load_skill_content(self, skill_id: str) -> Optional[str]:
        if skill_id not in self.SKILLS_METADATA:
            return None
        file_rel = self.SKILLS_METADATA[skill_id]["file"]
        skill_path = self.skills_dir / file_rel
        if skill_path.exists():
            return skill_path.read_text(encoding="utf-8")
        return None

    def get_skill_instructions_for_prompt(self, prompt: str, token_budget: int = 1500) -> str:
        """
        Dynamically extracts concise instructions from only matched skills.
        """
        matched = self.match_relevant_skills(prompt, max_skills=2)
        chunks = []
        for item in matched:
            content = self.load_skill_content(item["id"])
            if content:
                # Extract up to 2000 chars per skill
                summary = content[:2000]
                chunks.append(f"### Skill: {item['title']}\n{summary}")

        return "\n\n".join(chunks)
