# TypeScript Strict Typing

## Purpose
Enforce compile-time safety and self-documenting code.

## When to Use
Any TS project, interface modeling, or refactoring.

## Workflow
1. Enable strict mode
2. Define precise union and interface types
3. Eliminate 'any' types
4. Compile with tsc --noEmit.

## Best Practices
Use discriminated unions for state. Leverage type narrowing.

## Common Failures & Pitfalls
Overusing 'as unknown as any', ignoring tsconfig path aliases.

## Verification Checklist
- [ ] No 'any' assertions
- [ ] Strict null checks enabled
- [ ] Clean tsc build.
