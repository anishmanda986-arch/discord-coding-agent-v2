# MongoDB Document Modeling

## Purpose
Design flexible document schemas and aggregation pipelines.

## When to Use
Working with NoSQL collections and document stores.

## Workflow
1. Model documents according to access patterns
2. Add compound indexes
3. Execute atomic updates.

## Best Practices
Avoid unbounded array growth. Use projection to limit returned fields.

## Common Failures & Pitfalls
Unindexed queries, huge single documents (>16MB).

## Verification Checklist
- [ ] Compound indexes created
- [ ] Atomic updates used.
