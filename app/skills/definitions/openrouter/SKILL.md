# OpenRouter & AI Gateway Integration

## Purpose
Integrate OpenRouter and OpenAI-compatible multi-model providers.

## When to Use
Configuring /api, fetching /models, and streaming completions.

## Workflow
1. Validate base URL
2. Fetch and cache /models
3. Send chat completions
4. Stream progress updates.

## Best Practices
Cache model metadata for 24 hours. Fallback gracefully on 404.

## Common Failures & Pitfalls
Querying /models on every prompt, exposing user API keys.

## Verification Checklist
- [ ] Models cached
- [ ] Streaming progress working
- [ ] Fallback handling tested.
