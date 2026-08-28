# DevOps & Deployment Pipelines

## Purpose
Automate build, test, and deployment workflows.

## When to Use
Setting up CI/CD pipelines, Cloud Run deployment, health checks.

## Workflow
1. Define pipeline stages (Lint -> Test -> Build -> Deploy)
2. Inject environment secrets
3. Configure rollback triggers.

## Best Practices
Fail fast in CI. Keep builds reproducible.

## Common Failures & Pitfalls
Broken dependencies in CI, unmonitored deployments.

## Verification Checklist
- [ ] Pipeline automated
- [ ] Health check endpoint live.
