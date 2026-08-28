# Automated Testing & QA

## Purpose
Write comprehensive unit, integration, and property tests.

## When to Use
Writing test suites, running /test, or verifying bug fixes.

## Workflow
1. Identify happy paths & edge cases
2. Write unit tests with assertions
3. Execute via test runner (pytest/jest)
4. Verify code coverage.

## Best Practices
Tests must be deterministic and isolated. Mock external network calls.

## Common Failures & Pitfalls
Flaky timing-dependent tests, tests mutating shared state.

## Verification Checklist
- [ ] All tests passing
- [ ] Edge cases covered
- [ ] Mocked network calls.
