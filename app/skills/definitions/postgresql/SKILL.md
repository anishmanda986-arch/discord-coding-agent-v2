# PostgreSQL Optimization & Schemas

## Purpose
Leverage advanced PostgreSQL features, JSONB, and connection pooling.

## When to Use
Working with PostgreSQL or Cloud SQL databases.

## Workflow
1. Define schema with constraints
2. Use asyncpg/psycopg3 connection pools
3. Profile with EXPLAIN ANALYZE.

## Best Practices
Use connection poolers. Index JSONB with GIN where searched.

## Common Failures & Pitfalls
Exhausting max connections, unindexed JSONB queries.

## Verification Checklist
- [ ] Connection pool configured
- [ ] Foreign keys indexed.
