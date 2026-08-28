# Performance Optimization & Benchmarking

## Purpose
Maximize throughput and minimize latency across the stack.

## When to Use
Optimizing agent loops, caching, database queries, and async I/O.

## Workflow
1. Profile bottlenecks
2. Implement caching (L1/L2)
3. Batch parallel operations
4. Measure speedup.

## Best Practices
Optimize data transfer before compute. Avoid serial requests.

## Common Failures & Pitfalls
Premature optimization, unmeasured assumptions.

## Verification Checklist
- [ ] Parallel async I/O
- [ ] Caching active
- [ ] Latency reduced.
