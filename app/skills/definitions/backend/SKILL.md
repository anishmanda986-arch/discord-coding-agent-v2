# Backend Engineering

## Purpose
Design scalable, secure, and resilient server-side services.

## When to Use
Building APIs, background workers, database models, and authentication.

## Workflow
1. Define schema & routes
2. Implement business logic in services
3. Add authentication/authorization
4. Write integration tests.

## Best Practices
Validate all inputs with Pydantic/Zod. Use connection pooling. Log structured JSON.

## Common Failures & Pitfalls
SQL injection, missing rate limits, blocking synchronous I/O.

## Verification Checklist
- [ ] Input validation active
- [ ] Async I/O utilized
- [ ] Structured logging enabled.
