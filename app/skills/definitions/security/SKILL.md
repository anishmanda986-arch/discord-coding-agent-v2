# Application Security & Hardening

## Purpose
Protect applications against vulnerabilities, injection, and data leakage.

## When to Use
Reviewing code, handling inputs, managing credentials.

## Workflow
1. Validate and sanitize all inputs
2. Enforce authentication & authorization
3. Redact secrets from logs and outputs
4. Jail filesystem paths.

## Best Practices
Never trust user input. Use constant-time comparison for secrets.

## Common Failures & Pitfalls
Path traversal (../), hardcoded credentials, command injection.

## Verification Checklist
- [ ] Path validation enforced
- [ ] Secret redaction active
- [ ] Commands sanitized.
