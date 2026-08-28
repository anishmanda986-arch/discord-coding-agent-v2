# Python 3.12+ Async & Modern Architecture

## Purpose
Write fast, type-hinted, and idiomatic Python applications.

## When to Use
Building Python backend services, bots, and CLI tools.

## Workflow
1. Use type hints throughout
2. Leverage asyncio for concurrent I/O
3. Use dataclasses and Pydantic
4. Test with pytest.

## Best Practices
Avoid blocking calls inside async event loops. Use context managers.

## Common Failures & Pitfalls
Running time.sleep() in async functions, mutable default arguments.

## Verification Checklist
- [ ] Async/await clean
- [ ] Type annotations checked
- [ ] Pytest passes.
