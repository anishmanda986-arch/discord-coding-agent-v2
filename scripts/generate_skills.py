import os
from pathlib import Path

SKILLS = {
    "software-engineering": {
        "title": "Software Engineering Principles",
        "purpose": "Apply solid architectural patterns, modularity, and high cohesion.",
        "when_to_use": "Whenever designing multi-file features, refactoring, or structuring code.",
        "workflow": "1. Understand requirements\n2. Design clean interfaces\n3. Implement incrementally\n4. Verify tests.",
        "best_practices": "Keep functions under 40 lines. Prefer pure functions. Name variables descriptively.",
        "common_failures": "Monolithic files, global mutable state, tight coupling.",
        "checklist": "- [ ] Interfaces defined\n- [ ] Single responsibility followed\n- [ ] No hardcoded secrets."
    },
    "web-development": {
        "title": "Modern Web Development",
        "purpose": "Build performant, secure, and standards-compliant web applications.",
        "when_to_use": "For client-server architectures, REST/GraphQL APIs, and web frontends.",
        "workflow": "1. Define API contracts\n2. Implement backend handlers\n3. Build responsive UI\n4. Connect with error handling.",
        "best_practices": "Use proper HTTP status codes. Handle loading and error states gracefully.",
        "common_failures": "Missing CORS headers, unhandled 500 errors, layout shifts.",
        "checklist": "- [ ] HTTP verbs matched to actions\n- [ ] Responsive on mobile\n- [ ] Validation on both ends."
    },
    "frontend": {
        "title": "Frontend Engineering",
        "purpose": "Create fast, accessible, and responsive user interfaces.",
        "when_to_use": "When implementing UI components, layouts, styling, and client state.",
        "workflow": "1. Break UI into components\n2. Style with Tailwind CSS\n3. Manage local/global state\n4. Add keyboard accessibility.",
        "best_practices": "Use semantic HTML. Maintain optical hierarchy and sufficient contrast.",
        "common_failures": "Uncontrolled re-renders, hardcoded px spacing, broken mobile layouts.",
        "checklist": "- [ ] Accessible colors\n- [ ] Touch targets >= 44px\n- [ ] Fast render performance."
    },
    "backend": {
        "title": "Backend Engineering",
        "purpose": "Design scalable, secure, and resilient server-side services.",
        "when_to_use": "Building APIs, background workers, database models, and authentication.",
        "workflow": "1. Define schema & routes\n2. Implement business logic in services\n3. Add authentication/authorization\n4. Write integration tests.",
        "best_practices": "Validate all inputs with Pydantic/Zod. Use connection pooling. Log structured JSON.",
        "common_failures": "SQL injection, missing rate limits, blocking synchronous I/O.",
        "checklist": "- [ ] Input validation active\n- [ ] Async I/O utilized\n- [ ] Structured logging enabled."
    },
    "fullstack": {
        "title": "Fullstack Application Architecture",
        "purpose": "Coordinate frontend and backend seamlessly with end-to-end type safety.",
        "when_to_use": "Building complete web apps, SaaS dashboards, or multi-tier services.",
        "workflow": "1. Scaffold project structure\n2. Implement database models & migrations\n3. Create API routes\n4. Build client views\n5. Test end-to-end.",
        "best_practices": "Share types between client and server. Handle offline/network disruptions.",
        "common_failures": "Mismatched API payload schemas, duplicate logic, exposed server secrets.",
        "checklist": "- [ ] Unified schema types\n- [ ] End-to-end tests passing\n- [ ] Clean build command."
    },
    "react": {
        "title": "React Component & State Architecture",
        "purpose": "Build reusable, reactive React components using modern hooks and patterns.",
        "when_to_use": "Developing React or Next.js applications.",
        "workflow": "1. Design component hierarchy\n2. Manage state with useState/useReducer\n3. Memoize heavy computations\n4. Test with React Testing Library.",
        "best_practices": "Avoid useEffect for computed state. Keep component files modular.",
        "common_failures": "Infinite effect loops, stale closures, missing key props in lists.",
        "checklist": "- [ ] Pure render logic\n- [ ] Proper dependency arrays\n- [ ] Error boundaries in place."
    },
    "nextjs": {
        "title": "Next.js Framework Master",
        "purpose": "Harness Next.js App Router, Server Components, and SSR capabilities.",
        "when_to_use": "Building production React fullstack apps with Next.js.",
        "workflow": "1. Configure app directory routes\n2. Use React Server Components by default\n3. Mark interactive components with 'use client'\n4. Optimize metadata & images.",
        "best_practices": "Fetch data directly in Server Components. Secure environment variables.",
        "common_failures": "Accidental 'use client' on everything, route handler runtime errors.",
        "checklist": "- [ ] Correct server/client boundary\n- [ ] Dynamic routes validated\n- [ ] Fast build time."
    },
    "typescript": {
        "title": "TypeScript Strict Typing",
        "purpose": "Enforce compile-time safety and self-documenting code.",
        "when_to_use": "Any TS project, interface modeling, or refactoring.",
        "workflow": "1. Enable strict mode\n2. Define precise union and interface types\n3. Eliminate 'any' types\n4. Compile with tsc --noEmit.",
        "best_practices": "Use discriminated unions for state. Leverage type narrowing.",
        "common_failures": "Overusing 'as unknown as any', ignoring tsconfig path aliases.",
        "checklist": "- [ ] No 'any' assertions\n- [ ] Strict null checks enabled\n- [ ] Clean tsc build."
    },
    "javascript": {
        "title": "Modern JavaScript ESNext",
        "purpose": "Write modern, clean, and idiomatic JavaScript.",
        "when_to_use": "Writing Node.js scripts, web apps, and utility functions.",
        "workflow": "1. Use ES Modules (import/export)\n2. Handle async with async/await\n3. Use structuredClone and modern built-ins.",
        "best_practices": "Avoid mutations. Use const by default.",
        "common_failures": "Unhandled promise rejections, callback hell.",
        "checklist": "- [ ] All promises caught or awaited\n- [ ] Clean module exports."
    },
    "python": {
        "title": "Python 3.12+ Async & Modern Architecture",
        "purpose": "Write fast, type-hinted, and idiomatic Python applications.",
        "when_to_use": "Building Python backend services, bots, and CLI tools.",
        "workflow": "1. Use type hints throughout\n2. Leverage asyncio for concurrent I/O\n3. Use dataclasses and Pydantic\n4. Test with pytest.",
        "best_practices": "Avoid blocking calls inside async event loops. Use context managers.",
        "common_failures": "Running time.sleep() in async functions, mutable default arguments.",
        "checklist": "- [ ] Async/await clean\n- [ ] Type annotations checked\n- [ ] Pytest passes."
    },
    "android": {
        "title": "Android Application Development",
        "purpose": "Build robust Android applications using Gradle and modern Android APIs.",
        "when_to_use": "Android project inspection, build fixes, or Kotlin code.",
        "workflow": "1. Check AndroidManifest.xml\n2. Configure build.gradle dependencies\n3. Implement activities/fragments\n4. Test with Gradle.",
        "best_practices": "Handle configuration changes. Follow material design guidelines.",
        "common_failures": "Missing permissions in manifest, main thread network calls.",
        "checklist": "- [ ] Manifest updated\n- [ ] Gradle builds without errors."
    },
    "kotlin": {
        "title": "Kotlin & Jetpack Compose",
        "purpose": "Write idiomatic Kotlin with coroutines and declarative UI.",
        "when_to_use": "Kotlin services or Jetpack Compose apps.",
        "workflow": "1. Use data classes & sealed classes\n2. Handle concurrency with CoroutineScope\n3. Compose UI declaratively.",
        "best_practices": "Leverage null-safety operators. Use StateFlow for reactive state.",
        "common_failures": "Leaking coroutine scopes, improper Compose recompositions.",
        "checklist": "- [ ] Coroutines structured\n- [ ] Null safety verified."
    },
    "discord": {
        "title": "Discord Bot & Interaction Engineering",
        "purpose": "Build interactive, resilient Discord bots using discord.py 2.x.",
        "when_to_use": "Implementing Discord commands, embeds, modals, and message handlers.",
        "workflow": "1. Setup discord.ext.commands.Bot\n2. Register slash commands (/api, /test, etc.)\n3. Handle on_message for natural conversation\n4. Format status updates with embeds.",
        "best_practices": "Always defer interactions before heavy operations. Never log bot tokens.",
        "common_failures": "Interaction timeout (exceeding 3 seconds without defer), rate limit bans.",
        "checklist": "- [ ] Interaction deferral active\n- [ ] Channel permission checks\n- [ ] Embeds formatted cleanly."
    },
    "api-integration": {
        "title": "API Integration & Client Design",
        "purpose": "Integrate third-party REST/GraphQL APIs with retries and rate limits.",
        "when_to_use": "Connecting to external services, OpenRouter, GitHub, Stripe, etc.",
        "workflow": "1. Normalize base URLs\n2. Build typed request/response models\n3. Implement exponential backoff\n4. Test with mock and live endpoints.",
        "best_practices": "Respect Retry-After headers. Redact tokens from error messages.",
        "common_failures": "Hardcoded timeouts, double slash in URLs, unredacted secrets.",
        "checklist": "- [ ] URL normalization active\n- [ ] Retries on 429/5xx only\n- [ ] Secrets redacted."
    },
    "openrouter": {
        "title": "OpenRouter & AI Gateway Integration",
        "purpose": "Integrate OpenRouter and OpenAI-compatible multi-model providers.",
        "when_to_use": "Configuring /api, fetching /models, and streaming completions.",
        "workflow": "1. Validate base URL\n2. Fetch and cache /models\n3. Send chat completions\n4. Stream progress updates.",
        "best_practices": "Cache model metadata for 24 hours. Fallback gracefully on 404.",
        "common_failures": "Querying /models on every prompt, exposing user API keys.",
        "checklist": "- [ ] Models cached\n- [ ] Streaming progress working\n- [ ] Fallback handling tested."
    },
    "database": {
        "title": "Database Schema & Query Design",
        "purpose": "Design efficient schemas, indexes, and transactions.",
        "when_to_use": "Adding database tables, optimizing queries, writing migrations.",
        "workflow": "1. Design normalized tables\n2. Add indexes on foreign keys & filter columns\n3. Write safe parameterized queries.",
        "best_practices": "Always use parameterized queries. Enable WAL mode on SQLite.",
        "common_failures": "Missing indexes causing table scans, N+1 query problems.",
        "checklist": "- [ ] Parameterized queries\n- [ ] Indexes added\n- [ ] WAL mode enabled."
    },
    "postgresql": {
        "title": "PostgreSQL Optimization & Schemas",
        "purpose": "Leverage advanced PostgreSQL features, JSONB, and connection pooling.",
        "when_to_use": "Working with PostgreSQL or Cloud SQL databases.",
        "workflow": "1. Define schema with constraints\n2. Use asyncpg/psycopg3 connection pools\n3. Profile with EXPLAIN ANALYZE.",
        "best_practices": "Use connection poolers. Index JSONB with GIN where searched.",
        "common_failures": "Exhausting max connections, unindexed JSONB queries.",
        "checklist": "- [ ] Connection pool configured\n- [ ] Foreign keys indexed."
    },
    "mongodb": {
        "title": "MongoDB Document Modeling",
        "purpose": "Design flexible document schemas and aggregation pipelines.",
        "when_to_use": "Working with NoSQL collections and document stores.",
        "workflow": "1. Model documents according to access patterns\n2. Add compound indexes\n3. Execute atomic updates.",
        "best_practices": "Avoid unbounded array growth. Use projection to limit returned fields.",
        "common_failures": "Unindexed queries, huge single documents (>16MB).",
        "checklist": "- [ ] Compound indexes created\n- [ ] Atomic updates used."
    },
    "redis": {
        "title": "Redis In-Memory Caching & Queues",
        "purpose": "Implement sub-millisecond caching, rate limiting, and pub/sub.",
        "when_to_use": "Building distributed caches, rate limiters, or job queues.",
        "workflow": "1. Choose appropriate data structures (String, Hash, Sorted Set)\n2. Set explicit TTLs\n3. Use pipeline for batching.",
        "best_practices": "Always set TTL on cache keys to prevent memory leaks.",
        "common_failures": "KEYS * command blocking redis, forgetting TTL.",
        "checklist": "- [ ] TTL on all cache entries\n- [ ] Non-blocking commands used."
    },
    "testing": {
        "title": "Automated Testing & QA",
        "purpose": "Write comprehensive unit, integration, and property tests.",
        "when_to_use": "Writing test suites, running /test, or verifying bug fixes.",
        "workflow": "1. Identify happy paths & edge cases\n2. Write unit tests with assertions\n3. Execute via test runner (pytest/jest)\n4. Verify code coverage.",
        "best_practices": "Tests must be deterministic and isolated. Mock external network calls.",
        "common_failures": "Flaky timing-dependent tests, tests mutating shared state.",
        "checklist": "- [ ] All tests passing\n- [ ] Edge cases covered\n- [ ] Mocked network calls."
    },
    "debugging": {
        "title": "Systematic Root-Cause Debugging",
        "purpose": "Diagnose and fix software defects with precision.",
        "when_to_use": "When tests fail, builds break, or exceptions are thrown.",
        "workflow": "1. Reproduce failure\n2. Inspect stack trace\n3. Formulate hypothesis\n4. Apply minimal surgical fix\n5. Verify test passes.",
        "best_practices": "Fix the root cause, not just the symptom. Avoid shotgun debugging.",
        "common_failures": "Blindly adding try/except without understanding the error.",
        "checklist": "- [ ] Root cause identified\n- [ ] Targeted fix applied\n- [ ] Regression test added."
    },
    "security": {
        "title": "Application Security & Hardening",
        "purpose": "Protect applications against vulnerabilities, injection, and data leakage.",
        "when_to_use": "Reviewing code, handling inputs, managing credentials.",
        "workflow": "1. Validate and sanitize all inputs\n2. Enforce authentication & authorization\n3. Redact secrets from logs and outputs\n4. Jail filesystem paths.",
        "best_practices": "Never trust user input. Use constant-time comparison for secrets.",
        "common_failures": "Path traversal (../), hardcoded credentials, command injection.",
        "checklist": "- [ ] Path validation enforced\n- [ ] Secret redaction active\n- [ ] Commands sanitized."
    },
    "docker": {
        "title": "Docker Containerization",
        "purpose": "Containerize applications with multi-stage builds and minimal images.",
        "when_to_use": "Writing Dockerfile, docker-compose.yml, and sandbox execution.",
        "workflow": "1. Use lightweight base images (alpine/slim)\n2. Implement multi-stage builds\n3. Run as non-root user\n4. Configure health checks.",
        "best_practices": "Pin base image versions. Leverage layer caching.",
        "common_failures": "Running containers as root, huge image sizes (>1GB).",
        "checklist": "- [ ] Multi-stage build\n- [ ] Non-root user\n- [ ] .dockerignore configured."
    },
    "devops": {
        "title": "DevOps & Deployment Pipelines",
        "purpose": "Automate build, test, and deployment workflows.",
        "when_to_use": "Setting up CI/CD pipelines, Cloud Run deployment, health checks.",
        "workflow": "1. Define pipeline stages (Lint -> Test -> Build -> Deploy)\n2. Inject environment secrets\n3. Configure rollback triggers.",
        "best_practices": "Fail fast in CI. Keep builds reproducible.",
        "common_failures": "Broken dependencies in CI, unmonitored deployments.",
        "checklist": "- [ ] Pipeline automated\n- [ ] Health check endpoint live."
    },
    "github": {
        "title": "GitHub Collaboration & Actions",
        "purpose": "Automate Git operations, Pull Requests, and GitHub integrations.",
        "when_to_use": "Cloning repositories, pushing branches, opening PRs.",
        "workflow": "1. Authenticate with GitHub token\n2. Create feature branch\n3. Commit with semantic message\n4. Create PR with summary.",
        "best_practices": "Never commit secrets. Write informative PR descriptions.",
        "common_failures": "Pushing to main branch directly, force-pushing without permission.",
        "checklist": "- [ ] Branch created\n- [ ] Commits atomic\n- [ ] No secrets committed."
    },
    "git": {
        "title": "Git Workflow & Version Control",
        "purpose": "Manage codebase version control cleanly and safely.",
        "when_to_use": "Tracking changes, generating diffs, branching, committing.",
        "workflow": "1. Check status\n2. Stage specific files\n3. Write descriptive commit\n4. Review unified diff.",
        "best_practices": "Atomic commits. Clean commit messages.",
        "common_failures": "Accidentally committing .env or build artifacts.",
        "checklist": "- [ ] .gitignore in place\n- [ ] Clean working tree."
    },
    "ui-ux": {
        "title": "UI/UX & Visual Craftsmanship",
        "purpose": "Design sophisticated, purposeful, accessible interfaces.",
        "when_to_use": "Creating UI layouts, cards, buttons, themes, typography.",
        "workflow": "1. Choose cohesive color palette (cool or warm neutrals)\n2. Establish typographic scale\n3. Maintain consistent 8px/16px rhythm\n4. Ensure WCAG AA contrast.",
        "best_practices": "Reject AI clichés (no purple gradients, no nested cards, no hero eyebrows).",
        "common_failures": "Low contrast gray text, inconsistent border radii, crowded layouts.",
        "checklist": "- [ ] WCAG AA compliant\n- [ ] Clean padding math\n- [ ] Consistent typography."
    },
    "performance": {
        "title": "Performance Optimization & Benchmarking",
        "purpose": "Maximize throughput and minimize latency across the stack.",
        "when_to_use": "Optimizing agent loops, caching, database queries, and async I/O.",
        "workflow": "1. Profile bottlenecks\n2. Implement caching (L1/L2)\n3. Batch parallel operations\n4. Measure speedup.",
        "best_practices": "Optimize data transfer before compute. Avoid serial requests.",
        "common_failures": "Premature optimization, unmeasured assumptions.",
        "checklist": "- [ ] Parallel async I/O\n- [ ] Caching active\n- [ ] Latency reduced."
    },
    "documentation": {
        "title": "Technical Documentation",
        "purpose": "Write clear, concise, and actionable documentation.",
        "when_to_use": "Creating README.md, API docs, setup guides, and inline docstrings.",
        "workflow": "1. Outline purpose & prerequisites\n2. Provide copy-paste setup commands\n3. Document environment variables\n4. Add troubleshooting guide.",
        "best_practices": "Keep instructions up to date. Avoid vague hand-waving.",
        "common_failures": "Missing required env vars in docs, outdated install steps.",
        "checklist": "- [ ] Setup steps verified\n- [ ] Env vars documented\n- [ ] Examples provided."
    }
}

def generate_all_skills():
    # Resolve relative to project root
    project_root = Path(__file__).resolve().parent.parent
    base_dir = project_root / "app" / "skills" / "definitions"
    base_dir.mkdir(parents=True, exist_ok=True)

    for skill_id, data in SKILLS.items():
        folder = base_dir / skill_id
        folder.mkdir(parents=True, exist_ok=True)
        file_path = folder / "SKILL.md"

        content = f"""# {data['title']}

## Purpose
{data['purpose']}

## When to Use
{data['when_to_use']}

## Workflow
{data['workflow']}

## Best Practices
{data['best_practices']}

## Common Failures & Pitfalls
{data['common_failures']}

## Verification Checklist
{data['checklist']}
"""
        file_path.write_text(content, encoding="utf-8")
        print(f"Generated {file_path}")

if __name__ == "__main__":
    generate_all_skills()
