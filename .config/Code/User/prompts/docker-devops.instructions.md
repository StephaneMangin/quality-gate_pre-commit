---
description: "Docker and DevOps standards: multi-stage builds, security, 12-factor app, health checks. Use when working on Dockerfiles, compose files, or CI/CD configuration."
applyTo: "**/{Dockerfile,docker-compose*.yml,docker-compose*.yaml,.dockerignore}"
---

# Docker & DevOps

- Use multi-stage builds to minimize image size
- Don't run containers as root
- Pin base image versions (avoid `latest` tag)
- Use `.dockerignore` to exclude unnecessary files
- Store configuration in environment variables (12-factor app)
- Health checks for containerized services
- Use `docker compose` for local development environments
