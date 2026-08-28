# API Integration & Client Design

## Purpose
Integrate third-party REST/GraphQL APIs with retries and rate limits.

## When to Use
Connecting to external services, OpenRouter, GitHub, Stripe, etc.

## Workflow
1. Normalize base URLs
2. Build typed request/response models
3. Implement exponential backoff
4. Test with mock and live endpoints.

## Best Practices
Respect Retry-After headers. Redact tokens from error messages.

## Common Failures & Pitfalls
Hardcoded timeouts, double slash in URLs, unredacted secrets.

## Verification Checklist
- [ ] URL normalization active
- [ ] Retries on 429/5xx only
- [ ] Secrets redacted.
