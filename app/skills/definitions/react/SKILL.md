# React Component & State Architecture

## Purpose
Build reusable, reactive React components using modern hooks and patterns.

## When to Use
Developing React or Next.js applications.

## Workflow
1. Design component hierarchy
2. Manage state with useState/useReducer
3. Memoize heavy computations
4. Test with React Testing Library.

## Best Practices
Avoid useEffect for computed state. Keep component files modular.

## Common Failures & Pitfalls
Infinite effect loops, stale closures, missing key props in lists.

## Verification Checklist
- [ ] Pure render logic
- [ ] Proper dependency arrays
- [ ] Error boundaries in place.
