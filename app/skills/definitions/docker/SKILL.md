# Docker Containerization

## Purpose
Containerize applications with multi-stage builds and minimal images.

## When to Use
Writing Dockerfile, docker-compose.yml, and sandbox execution.

## Workflow
1. Use lightweight base images (alpine/slim)
2. Implement multi-stage builds
3. Run as non-root user
4. Configure health checks.

## Best Practices
Pin base image versions. Leverage layer caching.

## Common Failures & Pitfalls
Running containers as root, huge image sizes (>1GB).

## Verification Checklist
- [ ] Multi-stage build
- [ ] Non-root user
- [ ] .dockerignore configured.
