# Redis In-Memory Caching & Queues

## Purpose
Implement sub-millisecond caching, rate limiting, and pub/sub.

## When to Use
Building distributed caches, rate limiters, or job queues.

## Workflow
1. Choose appropriate data structures (String, Hash, Sorted Set)
2. Set explicit TTLs
3. Use pipeline for batching.

## Best Practices
Always set TTL on cache keys to prevent memory leaks.

## Common Failures & Pitfalls
KEYS * command blocking redis, forgetting TTL.

## Verification Checklist
- [ ] TTL on all cache entries
- [ ] Non-blocking commands used.
