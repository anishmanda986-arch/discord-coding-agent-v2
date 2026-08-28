# Database Schema & Query Design

## Purpose
Design efficient schemas, indexes, and transactions.

## When to Use
Adding database tables, optimizing queries, writing migrations.

## Workflow
1. Design normalized tables
2. Add indexes on foreign keys & filter columns
3. Write safe parameterized queries.

## Best Practices
Always use parameterized queries. Enable WAL mode on SQLite.

## Common Failures & Pitfalls
Missing indexes causing table scans, N+1 query problems.

## Verification Checklist
- [ ] Parameterized queries
- [ ] Indexes added
- [ ] WAL mode enabled.
